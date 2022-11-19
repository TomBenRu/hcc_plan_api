from fastapi import APIRouter, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pony.orm import db_session

from databases.enums import AuthorizationTypes
from databases.pony_models import Dispatcher, Admin
from databases.pydantic_models import Token, AdminBase, TeamBase, PersonBase, PersonCreateBase, PersonCreateRemoteBase, \
    DispatcherBase, TeamCreateBase, DispatcherShowBase, DispatcherCreateBase, PersonShowBase
from databases.services import find_user_by_email, create_new_team, create_dispatcher, get_project_from_user_id, \
    get_all_persons, get_all_project_teams, create_person
from oauth2_authentication import create_access_token, verify_supervisor_username, verify_supervisor_password, \
    verify_admin_username, verify_admin_password, verify_access_token
from utilities import utils

router = APIRouter(prefix='/admin', tags=['Admin'])


@router.get('/login')
def admin_login(email: str, password: str):
    admin: AdminBase = verify_admin_username(email)
    if not admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')
    if not verify_admin_password(password, admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'user_id': admin.id, 'authorization': AuthorizationTypes.admin.value})

    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/persons')
def get_persons(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id = token_data.id
    try:
        persons = get_all_persons(admin_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    return persons


@router.get('/teams')
def get_teams(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id = token_data.id
    try:
        teams = get_all_project_teams(admin_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    return teams


@router.get('/project')
def get_project(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id = token_data.id

    project = get_project_from_user_id(admin_id, Admin)
    return project


@router.post('/person')
def add_new_person(token: Token, person: PersonCreateRemoteBase):
    try:
        token_data = verify_access_token(token.access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id = token_data.id
    try:
        new_person = create_person(admin_id, person)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return new_person


@router.post('/dispatcher')
def add_new_dispatcher(person: PersonBase, token: Token):
    try:
        token_data = verify_access_token(token.access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id = token_data.id

    try:
        new_dispatcher = create_dispatcher(person=person)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return new_dispatcher


@router.post('/team')
def add_new_team(token: Token, team: TeamCreateBase, dispatcher: DispatcherShowBase):
    try:
        token_data = verify_access_token(token.access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    try:
        new_team = create_new_team(team=team, dispatcher=dispatcher)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f'Fehler: {e}')
    return new_team

