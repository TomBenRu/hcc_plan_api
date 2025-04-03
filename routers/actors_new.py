import pprint
from collections import defaultdict
from datetime import date, timedelta, datetime
from uuid import UUID

from fastapi import HTTPException, status, APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from starlette.responses import RedirectResponse, JSONResponse, HTMLResponse

from databases import services, schemas
from databases.enums import AuthorizationTypes, TimeOfDay
from oauth2_authentication import get_current_user_cookie, verify_actor_username
from utilities import send_mail
from utilities.send_mail import send_confirmed_avail_days

templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix='/actors_new', tags=['Actors'])


# Globale Konstanten
# Farben für die Icons
colors_times_of_day = {
    'morning': {
        'unchecked': 'gray-400',
        'checked': 'yellow-400'
    },
    'afternoon': {
        'unchecked': 'gray-400',
        'checked': 'orange-400'
    },
    'evening': {
        'unchecked': 'gray-400',
        'checked': 'red-500'
    }
}
# Farben für die Notifikation:
notification_colors = {
    'background': {
        'checked': 'green-100',
        'unchecked': 'red-100'
        },
    'border': {
        'checked': 'green-400',
        'unchecked': 'red-400'
        },
    'text': {
        'checked': 'green-700',
        'unchecked': 'red-700'
        }
}
# Übersetze die Periode ins Deutsche
period_translation = {
    "morning": "Morgen",
    "afternoon": "Nachmitt.",
    "evening": "Abend"
}

# Globale Variablen
selected_times: defaultdict[str, set] = defaultdict(set)  # Dictionary für ausgewählte Zeiten (später durch DB ersetzen)
user_notes = {}  # Dictionary für Anmerkungen (später durch DB ersetzen)


@router.get("/api/calendar-data", name="calendar_data", response_class=HTMLResponse)
async def get_calendar_data(request: Request):
    # Planungs-Perioden (müssen nach 'start' sortiert sein)
    plan_periods = [
        {'start': date(2024, 11, 1), 'end': date(2024, 11, 11), 'deadline': date(2024, 11, 10),
         'message': 'Planungsperiode 1\nErledige deine Einträge bitte bis zur Deadline.'},
        {'start': date(2024, 11, 12), 'end': date(2024, 11, 24), 'deadline': date(2024, 11, 23),
         'message': 'Planungsperiode 2'},
        {'start': date(2024, 11, 25), 'end': date(2024, 12, 10), 'deadline': date(2024, 12, 9),
         'message': 'Planungsperiode 3'},
        {'start': date(2024, 12, 11), 'end': date(2025, 1, 10), 'deadline': date(2025, 1, 9),
         'message': 'Planungsperiode 4'},
        {'start': date(2025, 1, 11), 'end': date(2025, 1, 20), 'deadline': date(2025, 1, 19),
         'message': 'Planungsperiode 5'},
        {'start': date(2025, 1, 21), 'end': date(2025, 2, 10), 'deadline': date(2025, 2, 9),
         'message': 'Planungsperiode 6'},
        {'start': date(2025, 2, 11), 'end': date(2025, 2, 20), 'deadline': date(2025, 2, 19),
         'message': 'Planungsperiode 7'},
        {'start': date(2025, 2, 21), 'end': date(2025, 3, 10), 'deadline': date(2025, 3, 9),
         'message': 'Planungsperiode 8'},
        {'start': date(2025, 3, 11), 'end': date(2025, 3, 20), 'deadline': date(2025, 3, 19),
         'message': 'Planungsperiode 9'},
        {'start': date(2025, 3, 21), 'end': date(2025, 4, 10), 'deadline': date(2025, 4, 9),
         'message': 'Planungsperiode 10'},
        {'start': date(2025, 4, 11), 'end': date(2025, 4, 20), 'deadline': date(2025, 4, 19),
         'message': 'Planungsperiode 11'},
        {'start': date(2025, 4, 21), 'end': date(2025, 5, 10), 'deadline': date(2025, 5, 9),
         'message': 'Planungsperiode 12'},
        {'start': date(2025, 5, 10), 'end': date(2025, 5, 31), 'deadline': date(2025, 5, 9),
         'message': 'Planungsperiode 13'},
        {'start': date(2025, 6, 1), 'end': date(2025, 6, 30), 'deadline': date(2025, 5, 9),
         'message': 'Planungsperiode 14'},
        {'start': date(2025, 7, 1), 'end': date(2025, 7, 31), 'deadline': date(2025, 6, 9),
         'message': 'Planungsperiode 15'}, ]

    # Tage aller Planperioden, gruppieren nach Monat und plan_periods
    grouped_dates = {}
    period_deadlines = {}
    period_messages = {}  # Dictionary für die Mitteilungen
    period_first_month = {}  # Speichert den ersten Monat jeder Periode

    token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    current_user_id = token_data.id

    plan_period_and_filled_in = services.PlanPeriod.get_open_plan_periods(current_user_id)

    for period in plan_period_and_filled_in:
        text_plan_period = f'{period.plan_period.start.strftime("%d.%m.%y")} - {period.plan_period.end.strftime("%d.%m.%y")}'
        period_deadlines[text_plan_period] = period.plan_period.deadline
        period_messages[text_plan_period] = period.plan_period.notes
        # Ersten Monat für jede Periode speichern
        period_first_month[text_plan_period] = period.plan_period.start.month

        for day in range((period.plan_period.end - period.plan_period.start).days + 1):
            day_date = period.plan_period.start + timedelta(days=day)
            if day_date.month not in grouped_dates:
                grouped_dates[day_date.month] = {
                    'year': day_date.year,
                    'periods': {}
                }
            if text_plan_period not in grouped_dates[day_date.month]['periods']:
                grouped_dates[day_date.month]['periods'][text_plan_period] = []
            grouped_dates[day_date.month]['periods'][text_plan_period].append(day_date)

    # Sortierte Perioden basierend auf der Startdatum
    sorted_periods = sorted(list({period for periods in grouped_dates.values()
                                  for period in periods['periods'].keys()}),
                            key=lambda x: (x.split(' - ')[0].split('.')[2],
                                           x.split(' - ')[0].split('.')[1],
                                           x.split(' - ')[0].split('.')[0]))
    pprint.pprint(sorted_periods)

    return templates.TemplateResponse("calendar_new.html", {
        "request": request,
        "grouped_dates": grouped_dates,
        "period_deadlines": period_deadlines,
        "period_messages": period_messages,
        "period_first_month": period_first_month,  # Übergebe die Information über den ersten Monat
        "selected_times": selected_times,  # Füge selected_times zum Template Context hinzu
        "user_notes": user_notes,  # Füge user_notes zum Template Context hinzu
        "sorted_periods": sorted_periods,  # Neue Variable für das Template,
        "colors_times_of_day": colors_times_of_day,
        "period_translation": period_translation
    })


@router.get("/index-new", response_class=HTMLResponse)
async def index_new(request: Request):
    """Zeigt die Hauptseite mit Login-Modal an"""
    return templates.TemplateResponse(
        "index_new.html",
        {"request": request}
    )


@router.post("/login-new")
async def login_new(request: Request):
    """Authentifiziert den Benutzer"""
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    # Hier Ihre Authentifizierungslogik einfügen
    if username == "admin" and password == "password":  # Beispiel-Credentials
        # Bei erfolgreicher Anmeldung den Kalender zurückgeben
        return await get_calendar_data(request)
    else:
        # Bei fehlgeschlagener Anmeldung einen JSON-Fehler zurückgeben
        return JSONResponse(
            content={
                "error": True,
                "error_message": "Anmeldedaten sind nicht korrekt"
            },
            status_code=401
        )


@router.get("/reset-password-new")
async def reset_password_new(request: Request):
    """Zeigt die Passwort-Reset-Seite an"""
    return templates.TemplateResponse(
        "reset_password_new.html",
        {"request": request}
    )


@router.post("/select-time-new")
async def select_time_new(request: Request):
    try:
        form = await request.form()
        date = form.get("date")
        period = form.get("period")
        print(f"select_time_new: {date}, {period}")

        if not date or not period:
            return templates.TemplateResponse(
                "notification_error.html",
                {
                    "request": request,
                    "message": "Datum oder Tageszeit fehlt"
                }
            )

        date_object = datetime.strptime(date, "%Y-%m-%d").date()
        time_of_day = TimeOfDay[period]
        print(f"select_time_new: {date_object}, {time_of_day}")

        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
        current_user_id = UUID(token_data.id)

        # Toggle selection status
        is_checked = False
        if date in selected_times and period in selected_times[date]:
            selected_times[date].remove(period)
            services.AvailDay.delete_avail_day(current_user_id, date_object, time_of_day)
        else:
            if date not in selected_times:
                selected_times[date] = set()
            selected_times[date].add(period)
            services.AvailDay.create_avail_day(current_user_id,
                                               schemas.AvailDayCreate(day=date_object, time_of_day=time_of_day))
            is_checked = True

        curr_icon_color = colors_times_of_day[period]['checked' if is_checked else 'unchecked']
        curr_notification_colors = {
            'background': notification_colors['background']['checked' if is_checked else 'unchecked'],
            'border': notification_colors['border']['checked' if is_checked else 'unchecked'],
            'text': notification_colors['text']['checked' if is_checked else 'unchecked']
        }

        return templates.TemplateResponse(
            "period_response_new.html",
            {
                "request": request,
                "date": date_object,
                "period": period,
                "period_translation": period_translation,
                "checked": is_checked,
                "curr_icon_color": curr_icon_color,
                "curr_notification_colors": curr_notification_colors
            }
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "notification_error.html",
            {
                "request": request,
                "message": str(e)
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "notification_error.html",
            {
                "request": request,
                "message": f"Ein unerwarteter Fehler ist aufgetreten: {e}"
            }
        )


@router.post("/load-period-notes-new")
async def load_period_notes_new(request: Request):
    form = await request.form()
    period = form.get("period")
    color = form.get("color")

    start_date, end_date = period.split(' - ')
    start_date = datetime.strptime(start_date, '%d.%m.%y').date()
    end_date = datetime.strptime(end_date, '%d.%m.%y').date()
    token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    current_user_id = UUID(token_data.id)

    message, deadline, plan_period_id = services.PlanPeriod.get_notes_and_deadline(
        start_date, end_date, current_user_id)
    notes = services.Availables.get_notes_from_person_planperiod(current_user_id, plan_period_id)


    print(f'load_period_notes_new: notes: {notes}, deadline: {deadline}')

    if period:
        return templates.TemplateResponse(
            "period_notes_new.html",
            {
                "request": request,
                "period": period,
                "deadline": deadline,
                "message": message,
                "notes": notes,
                "color": color
            }
        )
    return {"error": "Period not found"}


@router.post("/api/save-notes-new")
async def save_notes_new(request: Request):
    try:
        form = await request.form()
        period = form.get("period")
        notes = form.get("notes")
        success = True
        print(f"save_notes_new: {period}, {notes}")

        # Validiere die Eingaben
        if not period:
            return templates.TemplateResponse(
                "notification_error.html",
                {
                    "request": request,
                    "message": "Ungültige Eingabe"
                }
            )

        # Speichere oder lösche die Anmerkung
        if notes:
            user_notes[period] = notes
        else:
            if period in user_notes:
                del user_notes[period]
            success = False

        start_date, end_date = period.split(' - ')
        start_date = datetime.strptime(start_date, '%d.%m.%y').date()
        end_date = datetime.strptime(end_date, '%d.%m.%y').date()
        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
        current_user_id = UUID(token_data.id)
        _, _, plan_period_id = services.PlanPeriod.get_notes_and_deadline(start_date, end_date, current_user_id)
        services.Availables.update_notes_for_person_planperiod(current_user_id, plan_period_id, notes)



        return templates.TemplateResponse("notification_notes_new.html", {
            "request": request,
            "period": period,
            "success": success
        })
    except Exception as e:
        return templates.TemplateResponse(
            "notification_error.html",
            {
                "request": request,
                "message": f"Fehler beim Speichern: {str(e)}"
            }
        )
