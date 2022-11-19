import datetime

from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import EmailStr, json, BaseModel

from databases.database import Dispatcher
from databases.enums import AuthorizationTypes
from databases.pydantic_models import Token, TeamBase, PersonBase, ActorCreateBaseRemote, TokenData, PersonCreateBase, \
    PersonCreateRemoteBase
from databases.services import (create_actor__remote, find_user_by_email, create_new_plan_period, get_past_plan_periods,
                                change_status_planperiod, get_actors_in_dispatcher_teams, get_avail_days_from_actor,
                                get_teams_of_dispatcher, get_planperiods_last_recent_date, get_project_from_user_id)
from oauth2_authentication import (verify_supervisor_username, verify_supervisor_password, create_access_token,
                                   verify_access_token, verify_su_access_token,
                                   get_current_dispatcher)
from utilities import utils

router = APIRouter(prefix='/dispatcher', tags=['Dispatcher'])


@router.get('/login', response_model=Token)
def dispatcher_login(email: str, password: str):
    if not (dispatcher := find_user_by_email(email, Dispatcher)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    if not utils.verify(password, dispatcher.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'user_id': dispatcher.id,
                                             'authorization': AuthorizationTypes.dispatcher.value})
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/project')
def get_project(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    dispatcher_id = token_data.id

    project = get_project_from_user_id(dispatcher_id, Dispatcher)
    return project


@router.post('/actor')
def create_new_actor(person: PersonCreateRemoteBase, team: dict[str, str], token: Token):
    try:
        token_data = verify_access_token(token.access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')

    team_id = team['team_id']

    try:
        new_actor = create_actor__remote(person, team_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'dieser Fehler trat auf: {e}')

    return new_actor


@router.post('/planperiod')
def new_planperiod(access_token: str, team_id: str, date_start: str, date_end: str, deadline: str, notes: str = ''):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
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
        print('Exception:', e)
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')

    return new_plan_period


@router.get('/planperiods')
def get_planperiods(access_token: str, team_id: str, nbr_past_planperiods: int, only_not_closed: int):
    """nbr_past_planperiods: positiver Wert -> Anzahl zurückliegender Planperioden.
       0 -> alle Planperioden"""
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    dispatcher_id = int(token_data.id)
    nbr_past_planperiods = int(nbr_past_planperiods)
    only_not_closed = bool(only_not_closed)

    plan_periods = get_past_plan_periods(team_id, nbr_past_planperiods, only_not_closed)

    return plan_periods


@router.get('/pp_last_recent_date')
def get_planperiod_last_recent_date(access_token: str, team_id: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    dispatcher_id = int(token_data.id)

    date = get_planperiods_last_recent_date(team_id)
    return date


@router.get('/teams')
def get_teams(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    dispatcher_id = token_data.id
    teams = get_teams_of_dispatcher(dispatcher_id)
    return teams




@router.get('/status-planperiod')
def status_planperiod(access_token: str, plan_period_id: int, closed: int):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    dispatcher_id = int(token_data.id)

    plan_period_id = int(plan_period_id)
    closed = bool(closed)

    try:
        plan_period = change_status_planperiod(plan_period_id, closed, dispatcher_id)
    except KeyError as e:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Error: {e}')

    return plan_period


@router.get('/actors')
def get_clowns(access_token: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    dispatcher_id = token_data.id
    actors = get_actors_in_dispatcher_teams(dispatcher_id)
    return actors


@router.get('/avail_days')
def get_avail_days(access_token: str, actor_id: str):
    try:
        token_data = verify_access_token(access_token, authorization=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    dispatcher_id = token_data.id
    avail_days = get_avail_days_from_actor(actor_id=actor_id)
    return avail_days

