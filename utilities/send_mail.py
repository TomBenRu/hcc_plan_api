from email.message import EmailMessage
import smtplib
from uuid import UUID

import databases.pydantic_models as pm
import settings
from databases.services import delete_job_from_db, get_not_feedbacked_availables, get_planperiod, \
    get_persons__from_plan_period, get_avail_days__from_actor_planperiod

SEND_ADDRESS = settings.settings.send_address
SEND_PASSWORD = settings.settings.send_password
POST_AUSG_SERVER = settings.settings.post_ausg_server
SEND_PORT = settings.settings.send_port


def send_new_password(person: pm.Person, project: str, new_psw: str):
    send_to = person.email
    msg = EmailMessage()
    msg['From'] = SEND_ADDRESS
    msg['To'] = send_to
    msg['Subject'] = f'Account bei "{project}" Online-Planung'

    msg.set_content(f'Hallo {person.f_name} {person.l_name},\n\ndein neues Passwort für den Online-Zugang lautet:\n\n'
                    f'{new_psw}\n\n'
                    f'Viele Grüße\nTeam hcc-plan')
    with smtplib.SMTP(POST_AUSG_SERVER, SEND_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SEND_ADDRESS, SEND_PASSWORD)
        smtp.send_message(msg)

    return True


def send_remainder_confirmation(planperiod: pm.PlanPeriod, persons: list[pm.Person]):
    text_empfaenger = ', '.join([f'{p.f_name} {p.l_name}' for p in persons])
    send_to = planperiod.team.dispatcher.email
    msg = EmailMessage()
    msg['From'] = SEND_ADDRESS
    msg['To'] = send_to
    msg['Subject'] = 'hcc Remainder verschickt'
    msg.set_content(
        f'Hallo {planperiod.team.dispatcher.f_name} {planperiod.team.dispatcher.l_name},\n\n'
        f'es wurden Remainder verschickt.\n'
        f'Planungszeitraum: {planperiod.start.strftime("%d.%m.%y")} - {planperiod.end.strftime("%d.%m.%y")}\n'
        f'Empfänger: {text_empfaenger}\n\n'
        f'Team hcc-dispo'
    )
    with smtplib.SMTP(POST_AUSG_SERVER, SEND_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SEND_ADDRESS, SEND_PASSWORD)
        smtp.send_message(msg)


def send_remainder_deadline(plan_period_id: str):
    planperiod = get_planperiod(UUID(plan_period_id))
    persons = get_not_feedbacked_availables(plan_period_id)
    text_planperiod = f"Zeitraum: {planperiod.start.strftime('%d.%m.%y')} - {planperiod.end.strftime('%d.%m.%y')}"
    for person in persons:
        send_to = person.email
        msg = EmailMessage()
        msg['From'] = SEND_ADDRESS
        msg['To'] = send_to
        msg['Subject'] = f'Remainder: Abgabe deiner Spieloptionen'
        msg.set_content(f'Hallo {person.f_name} {person.l_name},\n\n'
                        f'heute ist die Deadline für die Abgabe deiner Spieloptionen.\n'
                        f'Es sind noch keine Rückmeldungen über den Online-Planungsservice von {person.project.name} '
                        f'für die folgende Planung eingegangen:\n\n'
                        f'- {text_planperiod}.\n\n'
                        f'Falls du dies bereits per Excell-Tabelle via Email getan hast, vergiss diesen Remainder.\n'
                        f'Andernfalls solltest du das noch heute erledigen, damit ich dich bei der Planung der '
                        f'Einsätze berücksichtigen kann.\n\n'
                        f'{planperiod.team.dispatcher.f_name} {planperiod.team.dispatcher.l_name}\n'
                        f'(Spielplanung {person.project.name})\n'
                        f'--- Diese Email wurde automatisch generiert. Bitte nicht antworten. ---')
        with smtplib.SMTP(POST_AUSG_SERVER, SEND_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SEND_ADDRESS, SEND_PASSWORD)
            smtp.send_message(msg)
    delete_job_from_db(plan_period_id)
    send_remainder_confirmation(planperiod, persons)
    return True


def send_avail_days_to_actors(plan_period_id: str):
    plan_period = get_planperiod(UUID(plan_period_id))
    persons = get_persons__from_plan_period(UUID(plan_period_id))
    time_of_day_explicit = {'v': 'Vormittag', 'n': 'Nachmittag', 'g': 'Ganztag'}
    persons_with_availables: list[tuple[pm.PersonShow, list[pm.AvailDayShow]]] = []
    for person in persons:
        if person.email != 'mail@thomas-ruff.de':
            continue
        avail_days_from_service = get_avail_days__from_actor_planperiod(person.id, UUID(plan_period_id))
        if avail_days_from_service is None:
            continue
        avail_days = sorted(avail_days_from_service, key=lambda x: x.day)
        persons_with_availables.append((person, avail_days))
        if avail_days:
            avail_days_txt = '\n'.join([f'{ad.day.strftime("%d.%m.%Y")} ({time_of_day_explicit[ad.time_of_day.value]})'
                                        for ad in avail_days])
        else:
            avail_days_txt = 'Keine Spieloptionen.'
        send_to = person.email
        msg = EmailMessage()
        msg['From'] = SEND_ADDRESS
        msg['To'] = send_to
        msg['Subject'] = f'Deine Spieloptionen: Planung von ' \
                         f'{plan_period.start.strftime("%d.%m.%Y")}-{plan_period.end.strftime("%d.%m.%Y")}'
        msg.set_content(f'Hallo {person.f_name} {person.l_name},\n\n'
                        f'für den im Betreff genannten Planungszeitraum können '
                        f'keine Spieloptionen mehr abgegeben werden.\n'
                        f'Du hast im Online-Portal folgende Tage/Zeiten angegeben, an denen du verfügbar bist:\n\n'
                        f'{avail_days_txt}\n\n'
                        f'{plan_period.team.dispatcher.f_name} {plan_period.team.dispatcher.l_name}\n'
                        f'(Spielplanung {person.project.name})\n'
                        f'--- Diese Email wurde automatisch generiert. Bitte nicht antworten. ---')
        with smtplib.SMTP(POST_AUSG_SERVER, SEND_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SEND_ADDRESS, SEND_PASSWORD)
            smtp.send_message(msg)
    send_online_availables_to_dispatcher(persons_with_availables, plan_period, plan_period.team.dispatcher)
    return True


def send_online_availables_to_dispatcher(persons_with_availables: list[tuple[pm.PersonShow, list[pm.AvailDayShow]]],
                                         plan_period: pm.PlanPeriod, dispatcher: pm.Person):
    """Die online abgegebenen Termine werden per E-Mail an den Dispatcher gesendet."""

    text_content = '\n'.join([f'{p.f_name} {p.l_name}: {", ".join([av_d.day.strftime("%d.%m.") + f" ({av_d.time_of_day.value})" for av_d in av])}'
                              for p, av in persons_with_availables])
    msg = EmailMessage()
    msg['From'] = SEND_ADDRESS
    msg['To'] = dispatcher.email
    msg['Subject'] = f'Abgegebene Termine für die Planperiode: ' \
                     f'{plan_period.start.strftime("%d.%m.%Y")}-{plan_period.end.strftime("%d.%m.%Y")}, ' \
                     f'Team {plan_period.team.name}'
    msg.set_content(f'{text_content}')
    with smtplib.SMTP(POST_AUSG_SERVER, SEND_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SEND_ADDRESS, SEND_PASSWORD)
        smtp.send_message(msg)
