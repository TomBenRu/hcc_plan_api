import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Request, Depends

from databases.enums import AuthorizationTypes
import databases.pydantic_models as pm
from databases.services import (create_new_plan_period,
                                change_status_planperiod, get_actors_in_dispatcher_teams, get_avail_days_from_actor,
                                get_planperiods_last_recent_date, get_project_from_user_id,
                                make_person__actor_of_team, get_teams_of_dispatcher, get_planperiods_of_team,
                                update_1_planperiod, delete_planperiod_from_team)
from oauth2_authentication import (verify_supervisor_username, verify_supervisor_password, create_access_token,
                                   verify_access_token, verify_su_access_token, verify_dispatcher_username, verify_user_password)
from utilities import utils

router = APIRouter(prefix='/dispatcher', tags=['Dispatcher'])


@router.get('/login', response_model=pm.Token)
def dispatcher_login(email: str, password: str):
    if not (user := verify_dispatcher_username(email)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    if not verify_user_password(password, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'user_id': user.id,
                                             'authorization': AuthorizationTypes.dispatcher.value})
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/project')
def get_project(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    project = get_project_from_user_id(user_id)
    return project


@router.post('/actor')
def create_new_actor(person: pm.Person, team: pm.Team, token: pm.Token):
    try:
        token_data = verify_access_token(token.access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id
    try:
        person = make_person__actor_of_team(person, team, user_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return person


@router.post('/planperiod')
def new_planperiod(access_token: str, team_id: str, date_start: str, date_end: str, deadline: str, notes: str = ''):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
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
def delete_planperiod(access_token: str, planperiod_id: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    try:
        deleted_planperiod = delete_planperiod_from_team(planperiod_id=UUID(planperiod_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return deleted_planperiod


@router.put('/planperiod')
def update_planperiod(token: pm.Token, planperiod: pm.PlanPeriod):
    try:
        token_data = verify_access_token(token.access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    try:
        planperiod_updated = update_1_planperiod(planperiod)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')
    return planperiod_updated


@router.get('/pp_last_recent_date')
def get_planperiod_last_recent_date(access_token: str, team_id: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials: {e}')
    user_id = token_data.id

    try:
        date = get_planperiods_last_recent_date(team_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')

    return date


@router.get('/teams')
def get_teams(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials: {e}')
    user_id = token_data.id
    try:
        teams = get_teams_of_dispatcher(user_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')
    return teams


@router.get('/planperiods')
def get_planperiods(access_token: str, team_id: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials: {e}')
    user_id = token_data.id
    try:
        planperiods = get_planperiods_of_team(team_id=UUID(team_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')
    return planperiods


@router.get('/actors')
def get_clowns(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials: {e}')
    user_id = token_data.id
    actors = get_actors_in_dispatcher_teams(user_id)
    return actors


@router.get('/avail_days')
def get_avail_days(access_token: str, actor_id: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    user_id = token_data.id
    avail_days = get_avail_days_from_actor(actor_id=user_id)
    return avail_days

