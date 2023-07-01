import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends

from databases import schemas
from databases.enums import AuthorizationTypes
from databases.services import create_new_team, get_project_from_user_id, \
    get_all_persons, get_all_project_teams, create_person, update_project_name, \
    delete_person_from_project, delete_team_from_project, delete_a_account, update_team_from_project, update_person
from oauth2_authentication import verify_access_token, oauth2_scheme

router = APIRouter(prefix='/admin', tags=['Admin'])


@router.get('/persons')
async def get_persons(access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id
    try:
        persons = get_all_persons(user_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    return persons


@router.get('/teams')
async def get_teams(access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id
    try:
        teams = get_all_project_teams(user_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    return teams


@router.get('/project')
async def get_project(access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    project = get_project_from_user_id(user_id)
    return project


@router.put('/project')
async def update_projekt_name(new_name: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    try:
        updated_project = update_project_name(user_id=user_id, project_name=new_name)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return updated_project


@router.post('/person')
async def add_new_person(person: schemas.PersonCreate, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        raise e
    user_id = token_data.id
    try:
        new_person = create_person(user_id, person)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return new_person


@router.post('/team')
async def add_new_team(team: schemas.TeamCreate, person: dict, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    try:
        new_team = create_new_team(team=team, person_id=person['id'])
    except Exception as e:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f'Fehler: {e}')
    return new_team


@router.put('/person')
async def update_a_person(person: schemas.PersonShow, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id: UUID = token_data.id

    try:
        updated_person = update_person(person, admin_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return updated_person


@router.delete('/person')
async def delete_person(person_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id: UUID = token_data.id

    try:
        deleted_person = delete_person_from_project(person_id=UUID(person_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f'Fehler: {e}')
    return deleted_person


@router.put('/team')
async def update_team(team_id: str, new_team_name: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id: UUID = token_data.id

    try:
        updated_team = update_team_from_project(team_id=UUID(team_id), new_team_name=new_team_name)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                             detail=f'Fehler: {e}')
    return updated_team


@router.delete('/team')
async def delete_team(team_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
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
async def delete_account(project_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.admin)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    admin_id: UUID = token_data.id

    try:
        deleted_account = delete_a_account(project_id=UUID(project_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f'Error: {e}')
    return deleted_account
