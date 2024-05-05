import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends

from databases import schemas, services
from databases.enums import AuthorizationTypes
from oauth2_authentication import verify_access_token, oauth2_scheme
from utilities.scheduler import scheduler
from utilities.send_mail import send_remainder_deadline, send_avail_days_to_actors

router = APIRouter(prefix='/dispatcher', tags=['Dispatcher'])


@router.get('/project')
def get_project(access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    project = services.Project.get_project_from_user_id(user_id)
    return project


@router.post('/planperiod')
async def new_planperiod(team_id: str, date_start: str, date_end: str, deadline: str, remainder: bool, notes: str = '',
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
        new_plan_period = services.PlanPeriod.create_new_plan_period(team_id, date_start, date_end, deadline, notes)
    except ValueError as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')
    if remainder:
        try:
            scheduler.remove_job(str(new_plan_period.id))
        except Exception as e:
            print(f'Job nicht vorhanden: {e}')
        try:
            services.APSchedulerJob.delete_job_from_db(str(new_plan_period.id))
        except Exception as e:
            print(f'Job nicht in DB vorhanden: {e}')
        run_date = datetime.datetime(new_plan_period.deadline.year, new_plan_period.deadline.month,
                                     new_plan_period.deadline.day) #  - datetime.timedelta(days=1)
        job = scheduler.add_job(func=send_remainder_deadline, trigger='date', run_date=run_date,
                                id=str(new_plan_period.id), args=[str(new_plan_period.id)])
        services.APSchedulerJob.add_job_to_db(job=job)

    return new_plan_period


@router.delete('/planperiod')
def delete_planperiod(planperiod_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    try:
        deleted_planperiod = services.PlanPeriod.delete_planperiod_from_team(planperiod_id=UUID(planperiod_id))
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')

    try:
        scheduler.remove_job(planperiod_id)
    except Exception as e:
        print(f'Fehler in Route /dispatcher/planperiod: {e}')
    print(f'rescheduled_jobs: {[j for j in scheduler.get_jobs()]}')
    return deleted_planperiod


@router.put('/planperiod')
def update_planperiod(planperiod: schemas.PlanPeriod, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error: {e}')
    user_id = token_data.id

    try:
        planperiod_updated = services.PlanPeriod.update_planperiod(planperiod)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Error: {e}')

    run_date = datetime.datetime(planperiod.deadline.year, planperiod.deadline.month,
                                 planperiod.deadline.day) - datetime.timedelta(days=1)
    try:
        job = scheduler.reschedule_job(str(planperiod.id), trigger='date', run_date=run_date)
        services.APSchedulerJob.update_job_in_db(job=job)
        print(f'rescheduled_jobs: {[j.__getstate__() for j in scheduler.get_jobs()]}')
    except Exception as e:
        print(f'Fehler in Route /dispatcher/planperiod: {e}')

    if planperiod_updated.closed:
        send_avail_days_to_actors(str(planperiod.id))

    return planperiod_updated


@router.get('/pp_last_recent_date')
async def get_planperiod_last_recent_date(team_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials: {e}')
    user_id = token_data.id

    try:
        date = services.PlanPeriod.get_planperiods_last_recent_date(team_id)
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
        teams = services.Team.get_teams_of_dispatcher(user_id)
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
        planperiods = services.PlanPeriod.get_planperiods_of_team(team_id=UUID(team_id))
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
    actors = services.Person.get_actors_in_dispatcher_teams(user_id)
    return actors


@router.get('/avail_days')
def get_avail_days(planperiod_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials - {e}')
    user_id = token_data.id
    avail_days = services.AvailDay.get_avail_days_from_planperiod(planperiod_id=UUID(planperiod_id))
    return avail_days


# nur fürs Testen:
@router.get('/not-feedbacked')
def not_feedbacked_availables(planperiod_id: str, access_token: str = Depends(oauth2_scheme)):
    try:
        token_data = verify_access_token(access_token, role=AuthorizationTypes.dispatcher)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'wrong cedentials - {e}')
    user_id = token_data.id
    not_feedbacked: list[schemas.Person] = services.Availables.get_not_feedbacked_availables(planperiod_id)
    return {'plan_period_id': planperiod_id, 'persons': not_feedbacked}


# @router.post('/create_remainder', response_model=schemas.APSchedulerJob)
# def create_remainder(planperiod_id: str, date: datetime.date):
#     print(f'in create_ramainder: {date}')
#     try:
#         scheduler.remove_job(job_id=planperiod_id)
#     except:
#         pass
#     try:
#         delete_job_from_db(planperiod_id)
#     except:
#         pass
#     job = scheduler.add_job(func=send_remainder_deadline, trigger='date',
#                       run_date=date, id=planperiod_id, args=[planperiod_id])
#     planpriod = get_planperiod(UUID(planperiod_id))
#     new_job = add_job_to_db(job)
#     return new_job


# @router.get('/persons-without-availables', response_model=list[schemas.Person])
# def persons_without_av(plan_period_id: str):
#     persons = get_not_feedbacked_availables(plan_period_id)
#     return persons
