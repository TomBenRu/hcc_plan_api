import datetime
import json
import pickle
import secrets
from typing import Optional, Union
from uuid import UUID

import apscheduler.job
from pony.orm import db_session
from pydantic import EmailStr

from databases import schemas, models
from utilities import utils
from .enums import TimeOfDay


class CustomError(Exception):
    pass


class Person:
    @staticmethod
    @db_session
    def get_user_by_id(user_id: UUID) -> schemas.PersonShow:
        person = models.Person[user_id]
        return schemas.PersonShow.model_validate(person)

    @staticmethod
    @db_session
    def create_person(admin_id: UUID, person: schemas.PersonCreate):
        if not (password := person.password):
            password = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(password)

        project = models.Person[admin_id].project
        person.project = project
        person.password = hashed_psw
        new_person = models.Person(f_name=person.f_name, l_name=person.l_name, artist_name=person.artist_name,
                                   email=person.email, username=person.username, password=person.password,
                                   project=project)
        return {'person': schemas.PersonShow.model_validate(new_person), 'password': password}

    @staticmethod
    @db_session
    def set_new_password(user_id: UUID):
        new_psw = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(new_psw)

        person_db = models.Person[user_id]
        person_db.password = hashed_psw
        return schemas.Person.model_validate(person_db), new_psw

    @staticmethod
    @db_session
    def delete_person_from_project(person_id: UUID):
        person_to_delete = models.Person[person_id]
        person_to_delete.delete()
        return schemas.Person.model_validate(person_to_delete)

    @staticmethod
    @db_session
    def update_person(person: schemas.PersonShow, admin_id: UUID) -> schemas.PersonShow:
        project = models.Person[admin_id].project
        person_in_db = models.Person.get_for_update(id=person.id)
        if person.project_of_admin:
            project.admin = person_in_db
        for t in person.teams_of_dispatcher:
            models.Team[t.id].dispatcher = person_in_db
        if person.team_of_actor:
            person_in_db.team_of_actor = models.Team[person.team_of_actor.id]
        else:
            person_in_db.team_of_actor = None
        person_in_db.set(f_name=person.f_name, l_name=person.l_name)
        return schemas.PersonShow.model_validate(person_in_db)

    @staticmethod
    @db_session
    def get_all_persons(admin_id: UUID) -> list[schemas.PersonShow]:
        try:
            persons = models.Person[admin_id].project_of_admin.persons
        except Exception as e:
            raise CustomError(f'Error: {e}')
        return [schemas.PersonShow.model_validate(p) for p in persons]

    @staticmethod
    @db_session
    def get_persons__from_plan_period(plan_period_id: UUID) -> list[schemas.PersonShow]:
        team_db = models.PlanPeriod.get_for_update(id=plan_period_id).team
        return [schemas.PersonShow.model_validate(p) for p in team_db.actors]

    @staticmethod
    @db_session
    def find_user_by_email(email: str) -> schemas.PersonShow | None:
        person = models.Person.get(lambda p: p.email.lower() == email.lower())
        if person:
            return schemas.PersonShow.model_validate(person)
        return None

    @staticmethod
    @db_session
    def set_new_actor_account_settings(person_id: UUID, new_email: EmailStr, new_password: str):
        user = models.Person[person_id]
        hashed_psw = utils.hash_psw(new_password)
        user.set(email=new_email, password=hashed_psw)
        return schemas.Person.model_validate(user)

    @staticmethod
    @db_session
    def get_actors_in_dispatcher_teams(dispatcher_id: UUID) -> list[schemas.PersonShow]:
        return [schemas.PersonShow.model_validate(p) for p in models.Person[dispatcher_id].teams_of_dispatcher.actors]


class Team:
    @staticmethod
    @db_session
    def update_team_from_project(team_id: UUID, new_team_name: str):
        team_to_update = models.Team[team_id]
        team_to_update.name = new_team_name
        return schemas.Team.model_validate(team_to_update)

    @staticmethod
    @db_session
    def delete_team_from_project(team_id: UUID):
        team_to_delete = models.Team[team_id]
        team_to_delete.delete()
        return schemas.Team.model_validate(team_to_delete)

    @staticmethod
    @db_session
    def get_all_project_teams(admin_id: UUID) -> list[schemas.Team]:
        try:
            teams = models.Person[admin_id].project_of_admin.teams
        except Exception as e:
            raise CustomError(f'Error: {e}')
        return [schemas.Team.model_validate(t) for t in teams]

    @staticmethod
    @db_session
    def get_teams_of_dispatcher(dispatcher_id: UUID) -> list[schemas.Team]:
        return [schemas.Team.model_validate(t) for t in models.Person[dispatcher_id].teams_of_dispatcher]

    @staticmethod
    @db_session
    def create_new_team(team: schemas.TeamCreate, person_id: str):
        person = models.Person[UUID(person_id)]
        new_team = models.Team(name=team.name, dispatcher=person)
        return schemas.TeamShow.model_validate(new_team)


class Project:
    @staticmethod
    @db_session
    def get_project_from_user_id(user_id) -> schemas.Project:
        project = models.Person[user_id].project
        return schemas.Project.model_validate(project)

    @staticmethod
    @db_session
    def update_project_name(user_id: UUID, project_name: str):
        project = models.Person[user_id].project_of_admin
        project.name = project_name
        return schemas.Project.model_validate(project)

    @staticmethod
    @db_session
    def create_account(project: schemas.ProjectCreate, person: schemas.PersonCreate):
        if not (password := person.password):
            password = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(password)

        new_project = models.Project(name=project.name)
        new_person = models.Person(f_name=person.f_name, l_name=person.l_name, email=person.email,
                                   username=person.username, password=hashed_psw,
                                   project=new_project, project_of_admin=new_project)

        return {'admin': schemas.PersonShow.model_validate(new_person), 'password': password}

    @staticmethod
    @db_session
    def delete_a_account(project_id: UUID):
        project_to_delete = models.Project[project_id]
        '''teams müssen vorab gelöscht werden, da in der Person-Entity im Feld "teams_of_dispatcher"
        cascade_delete wegen Sicherheitsgründen auf False gestellt ist.'''
        for team in project_to_delete.teams:
            team.delete()
        project_to_delete.delete()
        return schemas.Project.model_validate(project_to_delete)


class AvailDay:
    @staticmethod
    @db_session
    def available_days_to_db(avail_days: dict[str, str], user_id: int):
        available_days = {}
        for key, val in avail_days.items():
            date_av, plan_period_id = key.split('_')
            if date_av != 'infos':
                date_av = datetime.date(*[int(i) for i in date_av.split('-')])

            if plan_period_id not in available_days:
                available_days[plan_period_id] = {}
            available_days[plan_period_id][date_av] = val

        plan_periods = []

        for pp_id, dates in available_days.items():
            availables_in_db = models.Availables.get(
                lambda a: a.person == models.Person[user_id] and a.plan_period == models.PlanPeriod[pp_id])
            if availables_in_db:
                availables = availables_in_db
                availables.avail_days.clear()
            else:
                availables = models.Availables(plan_period=models.PlanPeriod[pp_id], person=models.Person[user_id])
            availables.notes = dates.pop('infos')

            av_days = {models.AvailDay(day=d, time_of_day=TimeOfDay(v), availables=availables)
                       for d, v in dates.items() if v != 'x'}
            plan_periods.append(schemas.PlanPeriod.model_validate(models.PlanPeriod[pp_id]))

        return plan_periods

    @staticmethod
    @db_session
    def get_avail_days_from_planperiod(planperiod_id: UUID) -> dict[UUID, dict[str, Union[str, schemas.AvailDay]]]:
        availabless = list(models.PlanPeriod[planperiod_id].availabless)
        avail_days = {availables.person.id: {'notes': availables.notes,
                                             'days': [schemas.AvailDay.model_validate(av_d) for av_d in
                                                      list(availables.avail_days)]}
                      for availables in availabless}
        return avail_days

    @staticmethod
    @db_session
    def get_avail_days__from_actor_planperiod(person_id, planperiod_id) -> list[schemas.AvailDayShow]:
        person = models.Person.get_for_update(id=person_id)
        availables = models.Availables.get_for_update(
            lambda av: av.person.id == person_id and av.plan_period.id == planperiod_id)
        print(
            '-----------------------------------------------------------------------------------------------------------')
        print(f'{person.f_name} {person.l_name}:\n{availables=}')
        print(
            '-----------------------------------------------------------------------------------------------------------')
        if not availables:
            return
        return [schemas.AvailDayShow.model_validate(ad) for ad in availables.avail_days]


class PlanPeriod:
    @staticmethod
    @db_session
    def get_open_plan_periods(user_id: UUID) -> list[schemas.PlanPerEtFilledIn]:
        person = models.Person.get(id=user_id)
        actor_team = person.team_of_actor
        plan_periods = models.PlanPeriod.select(lambda pp: pp.team == actor_team and not pp.closed)

        plan_p_et_filled_in: list[schemas.PlanPerEtFilledIn] = []
        for pp in plan_periods:
            if not pp.availabless.select(lambda av: av.person == person):
                filled_in = False
            else:
                filled_in = True if list(pp.availabless.select(lambda av: av.person == person).first().avail_days) else False

            plan_p_et_filled_in.append(schemas.PlanPerEtFilledIn(plan_period=schemas.PlanPeriodShow.model_validate(pp),
                                                                 filled_in=filled_in))
            plan_p_et_filled_in.sort(key=lambda pp_e_fi: pp_e_fi.plan_period.start)
        return plan_p_et_filled_in

    @staticmethod
    @db_session
    def get_planperiods_last_recent_date(team_id: str) -> Optional[datetime.date]:
        date = models.Team[UUID(team_id)].plan_periods.end
        if date:
            date = max(date)
        else:
            date = None
        return date

    @staticmethod
    @db_session
    def get_planperiods_of_team(team_id: UUID) -> list[schemas.PlanPeriod]:
        planperiods = models.Team[team_id].plan_periods
        return [schemas.PlanPeriod.model_validate(pp) for pp in planperiods]

    @staticmethod
    @db_session
    def update_planperiod(planperiod: schemas.PlanPeriod) -> schemas.PlanPeriod:
        planperiod_db = models.PlanPeriod[planperiod.id]

        planperiod_db.set(start=planperiod.start, end=planperiod.end, deadline=planperiod.deadline,
                          closed=planperiod.closed, notes=planperiod.notes)

        return schemas.PlanPeriod.model_validate(planperiod_db)

    @staticmethod
    @db_session
    def create_new_plan_period(team_id: str, date_start: datetime.date | None, date_end: datetime.date,
                               deadline: datetime.date, notes: str):
        max_date: datetime.date | None = None
        if planperiods := models.PlanPeriod.select(lambda pp: pp.team.id == UUID(team_id)):
            max_date: datetime.date = max(pp.end for pp in planperiods)
        if not date_start:
            if not max_date:
                raise ValueError('Sie müssen ein Startdatum angeben.')
            else:
                date_start = max_date + datetime.timedelta(days=1)

        elif max_date and date_start <= max_date:
            raise ValueError('Das Startdatum befindet sich in der letzten Planungsperiode.')
        if date_end < date_start:
            raise ValueError('Das Enddatum darf nicht vor dem Startdatum liegen.')

        plan_period = models.PlanPeriod(start=date_start, end=date_end, deadline=deadline, notes=notes,
                                        team=models.Team.get(lambda t: t.id == UUID(team_id)))
        return schemas.PlanPeriod.model_validate(plan_period)

    @staticmethod
    @db_session
    def get_planperiod(pp_id: UUID) -> schemas.PlanPeriod:
        return schemas.PlanPeriod.model_validate(models.PlanPeriod[pp_id])

    @staticmethod
    @db_session
    def delete_planperiod_from_team(planperiod_id: UUID):
        planperiod_to_delete = models.PlanPeriod[planperiod_id]
        deleted_planperiod = schemas.PlanPeriod.model_validate(planperiod_to_delete)
        planperiod_to_delete.delete()
        return deleted_planperiod


class Availables:
    @staticmethod
    @db_session
    def get_not_feedbacked_availables(plan_period_id: str) -> list[schemas.Person]:
        persons_with_availables = list([availables.person for availables in models.PlanPeriod[UUID(plan_period_id)].availabless
                                        if (availables.notes or availables.avail_days)])
        persons_without_availables = [person for person in models.PlanPeriod[UUID(plan_period_id)].team.actors
                                      if person not in persons_with_availables]
        return [schemas.Person.model_validate(p) for p in persons_without_availables]


class APSchedulerJob:
    @staticmethod
    @db_session
    def get_scheduler_jobs() -> list[schemas.APSchedulerJob]:
        jobs_db = models.APSchedulerJob.select()
        return [schemas.APSchedulerJob.model_validate(job) for job in jobs_db]

    @staticmethod
    @db_session
    def add_job_to_db(job: apscheduler.job.Job):
        print(f'add_job_to_db: {job=}')
        planperiod_db = models.PlanPeriod[UUID(job.id)]
        pickled_job = pickle.dumps(job)
        models.APSchedulerJob(plan_period=planperiod_db, job=pickled_job)

    @staticmethod
    @db_session
    def update_job_in_db(job: apscheduler.job.Job):
        job_db = models.APSchedulerJob.get(lambda j: str(j.plan_period.id) == job.id)
        job_db.job = pickle.dumps(job)

    @staticmethod
    @db_session
    def delete_job_from_db(job_id: str):
        plan_period_db = models.PlanPeriod.get(id=UUID(job_id))
        jobs_db_to_delete = models.APSchedulerJob.select(lambda asp: asp.plan_period == plan_period_db)
        for job_db_to_delete in jobs_db_to_delete:
            job_db_to_delete.delete()
        jobs_db_to_delete = [schemas.APSchedulerJob.model_validate(jd) for jd in jobs_db_to_delete]
        return jobs_db_to_delete


# todo: get_not_feedbacked_availables verbessern, sodass alle personen gelistet werden, die noch keine Einträge
#  in Terminen oder Notes gemacht haben.
