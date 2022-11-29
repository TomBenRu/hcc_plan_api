from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pony.orm import db_session

from databases.enums import AuthorizationTypes
import databases.pydantic_models as pm
from databases.services import find_user_by_email, create_new_team, get_project_from_user_id, \
    get_all_persons, get_all_project_teams, create_person, update_all_persons_in_project, update_project_name, \
    delete_person_from_project, delete_team_from_project, delete_a_account
from oauth2_authentication import create_access_token, verify_admin_username, verify_access_token, verify_user_password

router = APIRouter(prefix='/admin', tags=['Admin'])


@router.get('/login')
def admin_login(email: str, password: str):
    user: pm.Person = verify_admin_username(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')
    if not verify_user_password(password, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'user_id': user.id, 'authorization': AuthorizationTypes.admin.value})

    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/persons')
def get_persons(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id
    try:
        persons = get_all_persons(user_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    return persons


@router.get('/teams')
def get_teams(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id
    try:
        teams = get_all_project_teams(user_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    return teams


@router.get('/project')
def get_project(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    project = get_project_from_user_id(user_id)
    return project


@router.put('/project')
def update_projekt_name(access_token: str, new_name: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    try:
        updated_project = update_project_name(user_id=user_id, project_name=new_name)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return updated_project


@router.post('/person')
def add_new_person(token: pm.Token, person: pm.PersonCreate):
    pass
    try:
        token_data = verify_access_token(token.access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id
    try:
        new_person = create_person(user_id, person)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return new_person


@router.post('/team')
def add_new_team(token: pm.Token, team: pm.TeamCreate, person: dict):
    try:
        token_data = verify_access_token(token.access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    try:
        new_team = create_new_team(team=team, person_id=person['id'])
    except Exception as e:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f'Fehler: {e}')
    return new_team


@router.put('/update_all_persons')
def update_all_persons(token: pm.Token, all_persons: dict[str, pm.PersonShow]):
    try:
        token_data = verify_access_token(token.access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id: UUID = token_data.id

    try:
        persons = update_all_persons_in_project(list(all_persons.values()), admin_id=admin_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f'Fehler: {e}')
    return persons


@router.delete('/person')
def delete_person(access_token: str, person_id: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id: UUID = token_data.id

    try:
        deleted_person = delete_person_from_project(person_id=UUID(person_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f'Fehler: {e}')
    return deleted_person


@router.delete('/team')
def delete_team(access_token: str, team_id: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id: UUID = token_data.id

    try:
        deleted_team = delete_team_from_project(team_id=UUID(team_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f'Fehler: {e}')
    return deleted_team


@router.delete('/account')
def delete_account(access_token: str, project_id: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id: UUID = token_data.id

    try:
        deleted_account = delete_a_account(project_id=UUID(project_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f'Error: {e}')
    return deleted_account
