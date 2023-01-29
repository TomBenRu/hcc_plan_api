import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi_utils.tasks import repeat_every

from databases.enums import AuthorizationTypes
import databases.pydantic_models as pm
from databases.services import (create_new_plan_period, get_actors_in_dispatcher_teams,
                                get_planperiods_last_recent_date, get_project_from_user_id, get_teams_of_dispatcher,
                                get_planperiods_of_team, update_1_planperiod, delete_planperiod_from_team,
                                get_avail_days_from_planperiod, get_not_feedbacked_availables)
from oauth2_authentication import verify_access_token, oauth2_scheme

router = APIRouter(prefix='/dispatcher', tags=['Dispatcher'])


@router.get('/project')
def get_project(access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    project = get_project_from_user_id(user_id)
    return project


@router.post('/planperiod')
async def new_planperiod(team_id: str, date_start: str, date_end: str, deadline: str, notes: str = '',
                         access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials - {e}')
    dispatcher_id = token_data.id

    if not date_start:
        date_start = None
    else:
        date_start = datetime.date(*[int(v) for v in date_start.split('-')])
    date_end = datetime.date(*[int(v) for v in date_end.split('-')])
    deadline = datetime.date(*[int(v) for v in deadline.split('-')])
    try:
        new_plan_period = create_new_plan_period(team_id, date_start, date_end, deadline, notes)
    except ValueError as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')

    return new_plan_period


@router.delete('/planperiod')
def delete_planperiod(planperiod_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    try:
        deleted_planperiod = delete_planperiod_from_team(planperiod_id=UUID(planperiod_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return deleted_planperiod


@router.put('/planperiod')
def update_planperiod(planperiod: pm.PlanPeriod, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    try:
        planperiod_updated = update_1_planperiod(planperiod)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return planperiod_updated


@router.get('/pp_last_recent_date')
async def get_planperiod_last_recent_date(team_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials: {e}')
    user_id = token_data.id

    try:
        date = get_planperiods_last_recent_date(team_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')

    return date


@router.get('/teams')
async def get_teams(access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials: {e}')
    user_id = token_data.id
    try:
        teams = get_teams_of_dispatcher(user_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')
    return teams


@router.get('/planperiods')
def get_planperiods(team_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials: {e}')
    user_id = token_data.id
    try:
        planperiods = get_planperiods_of_team(team_id=UUID(team_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')
    return planperiods


@router.get('/actors')
def get_clowns(access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials: {e}')
    user_id = token_data.id
    actors = get_actors_in_dispatcher_teams(user_id)
    return actors


@router.get('/avail_days')
def get_avail_days(planperiod_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials - {e}')
    user_id = token_data.id
    avail_days = get_avail_days_from_planperiod(planperiod_id=UUID(planperiod_id))
    return avail_days


@router.on_event('startup')
@repeat_every(seconds=2, wait_first=True)
def remainder_availables():
    print('remainder')
    actors = get_actors_in_dispatcher_teams(UUID('80ea7175-497b-40bb-9b4d-3ffc78bb0bd2'))
    for person in actors:
        not_feedbacked = get_not_feedbacked_availables(person)
        print(f'{person.f_name=}, {not_feedbacked=}')

