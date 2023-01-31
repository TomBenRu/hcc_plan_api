from email.message import EmailMessage
import smtplib
from uuid import UUID

import databases.pydantic_models as pm
import settings
from databases.services import delete_job_from_db, get_not_feedbacked_availables, get_planperiod

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
        msg.set_content(f'Hallo {person.f_name} {person.l_name}, '
                        f'\n\n heute ist die Deadline für die Abgabe deiner Spieloptionen.\n'
                        f'Es sind noch keine Rückmeldungen über den Online-Planungsservice von {person.project.name} '
                        f'für die folgende Planung eingegangen:\n\n'
                        f'- {text_planperiod}.\n\n'
                        f'Falls du dies bereits per Excell-Tabelle via Email getan hast, vergiss diesen Remainder.\n'
                        f'Andernfalls solltest du das noch heute erledigen, damit ich dich bei der Planung der '
                        f'Einsätze berücksichtigen kann.\n\n'
                        f'{planperiod.team.dispatcher.f_name} {planperiod.team.dispatcher.l_name}\n'
                        f'(Spielplanung {person.project.name})')
        with smtplib.SMTP(POST_AUSG_SERVER, SEND_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SEND_ADDRESS, SEND_PASSWORD)
            smtp.send_message(msg)
    delete_job_from_db(plan_period_id)
    return True
