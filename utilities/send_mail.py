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
    for person in persons:
        if person.email != 'mail@thomas-ruff.de':
            continue
        avail_days = get_avail_days__from_actor_planperiod(person.id, plan_period_id)
        avail_days_txt = '\n'.join([f'{ad.day.strftime("%d.%m")} ({time_of_day_explicit[ad.time_of_day.value]})'
                                    for ad in avail_days])
        send_to = person.email
        msg = EmailMessage()
        msg['From'] = SEND_ADDRESS
        msg['To'] = send_to
        msg['Subject'] = f'Deine Spieloptionen: Planung von ' \
                         f'{plan_period.start.strftime("%d.%m.%Y")}-{plan_period.end.strftime("%d.%m.%Y")}'
        msg.set_content(f'Hallo {person.f_name} {person.l_name},\n\n'
                        f'du hast folgende Tage/Zeiten angegeben, an denen du verfügbar bist:\n'
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
    return True
