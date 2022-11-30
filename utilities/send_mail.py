from email.message import EmailMessage
import smtplib

import databases.pydantic_models as pm
import settings

SEND_ADDRESS = settings.settings.send_address
SEND_PASSWORD = settings.settings.send_password
POST_AUSG_SERVER = settings.settings.post_ausg_server
PORT = settings.settings.port


def send_new_password(person: pm.Person, project: str, new_psw: str):
    send_to = person.email
    msg = EmailMessage()
    msg['From'] = SEND_ADDRESS
    msg['To'] = send_to
    msg['Subject'] = f'Account bei "{project}" Online-Planung'

    msg.set_content(f'Hallo {person.f_name} {person.l_name},\n\ndein neues Passwort für den Online-Zugang lautet:\n\n'
                    f'{new_psw}\n\n'
                    f'Viele Grüße\nTeam hcc-plan')
    with smtplib.SMTP(POST_AUSG_SERVER, PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SEND_ADDRESS, SEND_PASSWORD)
        smtp.send_message(msg)

    return True
