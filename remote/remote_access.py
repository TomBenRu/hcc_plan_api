"""Der Supervisor legt den Erstzugang für den Admin an
   Der Admin kann neue Teams anlegen und  den zugehörigen Dispatcher (auch mehrere) einrichten."""

import requests
from pydantic import EmailStr
from requests.exceptions import ConnectionError
import time

from databases.database import local, from_outside
from databases.pydantic_models import PersonBase, PersonCreateBase, PersonCreateRemoteBase

# wenn die lokale Datenbank oder die Serverdatenbank von der lokalen API as verwendet wird:
if local:  # or (not local and from_outside):
    SERVER_ADDRESS = 'http://127.0.0.1:8000'
else:
    SERVER_ADDRESS = 'http://hcc-plan-curr.onrender.com'


def login_supervisor(username: str, password: str):
    print(f'{SERVER_ADDRESS}/su/login')
    connection_error = None
    t0 = time.time()
    while time.time() - t0 < 30:
        try:
            response = requests.get(f'{SERVER_ADDRESS}/su/login',
                                     params={'username': username, 'password': password})
            return response.json()
        except ConnectionError as e:
            print(e)
            connection_error = e
            time.sleep(0.2)
    raise connection_error


def create_account(name_project: str, f_name_admin: str, l_name_admin: str, email_admin: str, access_token: dict):
    response = requests.post(f'{SERVER_ADDRESS}/su/account',
                             json={'person': {'f_name': f_name_admin, 'l_name': l_name_admin, 'email': email_admin},
                                   'project': {'name': name_project}, 'access_token': access_token})
    return response.json()


def login_admin(email: str, password: str):
    response = requests.post(f'{SERVER_ADDRESS}/admin/login',
                             params={'username': email, 'password': password})
    return response.json()


def create_new_dispatcher(person: dict, token: dict):
    response = requests.post(f'{SERVER_ADDRESS}/admin/dispatcher',
                             json={'person': person, 'token': token})
    return response.json()


def create_new_team(name: str, admin_token: dict, dispatcher_id: str):
    response = requests.post(f'{SERVER_ADDRESS}/admin/team',
                             json={'team_name': {'name': name}, 'token': admin_token,
                                   'dispatcher': {'dispatcher_id': dispatcher_id}})
    return response.json()


def login_dispatcher(email: str, password: str) -> dict[str, str]:
    connection_error = None
    t0 = time.time()
    while time.time() - t0 < 30:
        try:
            response = requests.post(f'{SERVER_ADDRESS}/dispatcher/login',
                                     params={'email': email, 'password': password})
            return response.json()
        except ConnectionError as e:
            connection_error = e
            time.sleep(0.2)
    raise connection_error


def create_new_actor(person: PersonCreateRemoteBase, team_id: str, token: dict):
    response = requests.post(
        f'{SERVER_ADDRESS}/dispatcher/actor',
        json={'person': person.dict(), 'team': {'team_id': team_id}, 'token': token})
    return response.json()


def create_new_plan_period(access_token: str, team_id: str, date_start: str | None, date_end: str, deadline: str,
                           notes: str | None):

    date_start = '' if not date_start else date_start
    notes = '' if not notes else notes

    response = requests.post(f'{SERVER_ADDRESS}/dispatcher/new-planperiod',
                             params={'access_token': access_token, 'team_id': team_id, 'date_start': date_start,
                                     'date_end': date_end, 'deadline': deadline,
                                     'notes': notes})
    return response.json()





def get_planperiods(email_dispatcher: str, password_dispatcher: str, nbr_past_planperiods: int, only_not_closed: int):
    try:
        access_token = login_dispatcher(email_dispatcher, password_dispatcher)
    except Exception as e:
        raise e

    response = requests.get(f'{SERVER_ADDRESS}/dispatcher/get-planperiods',
                            params={'access_token': access_token, 'nbr_past_planperiods': nbr_past_planperiods,
                                    'only_not_closed': only_not_closed})
    return response.json()


def get_availables(email_dispatcher: str, password_dispatcher: str, nbr_past_planperiods: int, only_not_closed: int = 1):
    planperiods = get_planperiods(email_dispatcher, password_dispatcher, nbr_past_planperiods, only_not_closed)

    availables = {}

    for pp in planperiods:
        team = pp.pop('team')
        availables[(pp['id'], team['name'])] = {key: val for key, val in pp.items() if key not in ('id', 'notes')}

    return availables


def change_status_plan_period(email_dispatcher: str, password_dispatcher: str, plan_period_id: int, closed: int):
    try:
        access_token = login_dispatcher(email_dispatcher, password_dispatcher)
    except Exception as e:
        raise e

    response = requests.get(f'{SERVER_ADDRESS}/dispatcher/status-planperiod',
                            params={'access_token': access_token, 'plan_period_id': plan_period_id,
                                    'closed': closed})
    return response.json()



if __name__ == '__main__':
    """Server Postgresql on render.com
    {'new_admin': {'person': {'f_name': 'Anne', 'l_name': 'Feige', 'email': 'anne.feige@funmail.com', 'project': {'name': 'CleverClownCompany'}}, 'project': {'name': 'CleverClownCompany'}, 'id': '2dc00278-bb98-4e01-9a18-67bb91158572', 'created_at': '2022-11-14'}, 
    'password': 'tU67FkQhgdk'}
    {'dispatcher': {'person': {'f_name': 'Thomas', 'l_name': 'Ruff', 'email': 'mail@thomas-ruff.de', 'project': {'name': 'CleverClownCompany'}, 'id': '899c4b8e-8d41-4ee0-9d4c-e6028918ad2a'}, 'project': {'name': 'CleverClownCompany'}, 
    'id': 'bb980302-a94b-4dfb-8ce6-f0134aa1574f'}, 'password': 'ZACcIvpF4Kg'}
    {'name': 'Baden-Württemberg', 'project': {'name': 'CleverClownCompany'}, 'id': '708144ea-93c6-43ab-8335-367674383fb5', 'dispatcher': {'person': {'f_name': 'Thomas', 'l_name': 'Ruff', 'email': 'mail@thomas-ruff.de', 'project': {'name': 'CleverClownCompany'}, 'id': '899c4b8e-8d41-4ee0-9d4c-e6028918ad2a'}, 'project': {'name': 'CleverClownCompany'}, 'id': 'bb980302-a94b-4dfb-8ce6-f0134aa1574f'}, 'created_at': '2022-11-14'}
    {'actor': {'person': {'f_name': 'Rolf', 'l_name': 'Reichel', 'email': 'rolf.reichel@funmail.com', 'project': {'name': 'CleverClownCompany'}, 'id': '92d3fab7-76e8-4f65-b7d3-a1cf8f603419'}, 'team': {'name': 'Baden-Württemberg', 'project': {'name': 'CleverClownCompany'}}, 'id': '809c8c7c-beb5-46ef-9629-adf883c2ef24', 'active': True}, 
    'password': 'jrhxpplSIgA'}
    {'actor': {'person': {'f_name': 'Tanja', 'l_name': 'Thiele', 'email': 'tanja.thiele@funmail.com', 'project': {'name': 'CleverClownCompany'}, 'id': '03ac3ad9-af6c-4ee5-9a3b-7403b85c9709'}, 'team': {'name': 'Baden-Württemberg', 'project': {'name': 'CleverClownCompany'}}, 'id': '6d236888-0cb4-4bc1-bd3c-76ac01843cb8', 'active': True}, 
    'password': '2r2dqbhfgAw'}"""


    # {'new_admin': {'person': {'f_name': 'Anne', 'l_name': 'Feige', 'email': 'anne.feige@funmail.com', 'project': {'name': 'CleverClownCompany'}}, 'project': {'name': 'CleverClownCompany'}, 'id': 'db7c73a6-1ec1-4fe9-b284-89233515286a', 'created_at': '2022-11-14'},
    # 'password': 'w_CPEfQfgpE'}

    # {'dispatcher': {'person': {'f_name': 'Thomas', 'l_name': 'Ruff', 'email': 'mail@thomas-ruff.de', 'project': {'name': 'CleverClownCompany'}, 'id': '0dd57e4a-568e-4b38-95ad-e66727b6d737'}, 'project': {'name': 'CleverClownCompany'},
    # 'id': 'b0d37b75-e292-4475-8839-bde5eb0f69cb'}, 'password': 'eoHRZIxLfp0'}

    # {'name': 'Baden-Württemberg', 'project': {'name': 'CleverClownCompany'}, 'id': '5cb470d5-8f38-4779-9d9c-a5ad4501b6a3', 'dispatcher': {'person': {'f_name': 'Thomas', 'l_name': 'Ruff', 'email': 'mail@thomas-ruff.de', 'project': {'name': 'CleverClownCompany'}, 'id': '0dd57e4a-568e-4b38-95ad-e66727b6d737'}, 'project': {'name': 'CleverClownCompany'}, 'id': 'b0d37b75-e292-4475-8839-bde5eb0f69cb'}, 'created_at': '2022-11-14'}
    # {'name': 'Mainz', 'project': {'name': 'CleverClownCompany'}, 'id': '449ce906-3f1b-46ad-9d69-e9e32035be56', 'dispatcher': {'person': {'f_name': 'Thomas', 'l_name': 'Ruff', 'email': 'mail@thomas-ruff.de', 'project': {'name': 'CleverClownCompany'}, 'id': '0dd57e4a-568e-4b38-95ad-e66727b6d737'}, 'project': {'name': 'CleverClownCompany'}, 'id': 'b0d37b75-e292-4475-8839-bde5eb0f69cb'}, 'created_at': '2022-11-14'}

    # {'actor': {'person': {'f_name': 'Rolf', 'l_name': 'Reichel', 'email': 'rolf.reichel@funmail.com', 'project': {'name': 'CleverClownCompany'}, 'id': '9e6c411b-4623-42b4-abb8-16c5c64f9f04'}, 'team': {'name': 'Baden-Württemberg', 'project': {'name': 'CleverClownCompany'}}, 'id': '87b90b59-7972-4263-a724-97bdd2faeffd', 'active': True},
    # 'password': 'scWmHVqzUzA'}
    # {'actor': {'person': {'f_name': 'Tanja', 'l_name': 'Thiele', 'email': 'tanja.thiele@funmail.com', 'project': {'name': 'CleverClownCompany'}, 'id': '08607ee5-ef24-49fe-8ea1-cb148a716c2e'}, 'team': {'name': 'Baden-Württemberg', 'project': {'name': 'CleverClownCompany'}}, 'id': '622bc9ba-d995-4df5-b4c3-8bb7ed18c962', 'active': True},
    # 'password': '8Mp86W4W9ZM'}

    # planperiods = get_planperiods('beate.neumann@jokemail.de', 'AoBjrzdNpdA', 0, 0)
    # for pp in planperiods:
    #     print(pp)

    # availables = get_availables('beate.neumann@jokemail.de', 'AoBjrzdNpdA', 0)
    # for avail in availables.items():
    #     print(avail)

    # status_change = change_status_plan_period('beate.neumann@jokemail.de', 'AoBjrzdNpdA', plan_period_id=1, closed=0)
    # print(status_change)
    # actor_post()
    # actor_get()

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # su_login = login_supervisor('supervisor', 'mario')
    # print(su_login)
    #
    # admin = create_account('CleverClownCompany', 'Anne', 'Feige', 'anne.feige@funmail.com', su_login)
    # print(admin)

    admin_login = login_admin('anne.feige@funmail.com', 'w_CPEfQfgpE')
    print(admin_login)

    # new_dispatcher = create_new_dispatcher(person={'f_name': 'Thomas', 'l_name': 'Ruff', 'email': 'mail@thomas-ruff.de'},
    #                                        token=admin_login)
    # print(new_dispatcher)

    new_team = create_new_team('Mainz', admin_login, dispatcher_id='b0d37b75-e292-4475-8839-bde5eb0f69cb')
    print(new_team)

    # disp_token = login_dispatcher('mail@thomas-ruff.de', 'ZACcIvpF4Kg')
    # print(disp_token)

    # new_actor = create_new_actor(PersonCreateRemoteBase(f_name='Rolf', l_name='Reichel', email=EmailStr('rolf.reichel@funmail.com')),
    #                              team_id='708144ea-93c6-43ab-8335-367674383fb5', token=disp_token)
    # print(new_actor)

    # plan_period = create_new_plan_period(access_token=disp_token['access_token'],
    #                                      team_id='708144ea-93c6-43ab-8335-367674383fb5',
    #                                      date_start=None, date_end='2023-02-28', deadline='2022-12-15',
    #                                      notes='1. Planperiode.')
    # print(plan_period)


# todo: Zugang Admin remote und online.
# todo: Rechte Admin und Dispatcher ordnen (siehe Scriptkommentar)
