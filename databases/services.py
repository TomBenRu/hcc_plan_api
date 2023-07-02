import datetime
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
    def get_user_by_id(user_id: UUID) -> schemas.Person:
        with db_session:
            person = models.Person[user_id]
            return schemas.Person.from_orm(person)

    @staticmethod
    def create_person(admin_id: UUID, person: schemas.PersonCreate):
        if not (password := person.password):
            password = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(password)
        with db_session:
            project = models.Person[admin_id].project
            person.project = project
            person.password = hashed_psw
            new_person = models.Person(**person.dict())
            return {'person': schemas.PersonShow.from_orm(new_person), 'password': password}

    @staticmethod
    def set_new_password(user_id: UUID):
        new_psw = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(new_psw)
        with db_session:
            person_db = models.Person[user_id]
            person_db.password = hashed_psw
            return schemas.Person.from_orm(person_db), new_psw

    @staticmethod
    def delete_person_from_project(person_id: UUID):
        with db_session:
            person_to_delete = models.Person[person_id]
            person_to_delete.delete()
            return schemas.Person.from_orm(person_to_delete)

    @staticmethod
    def update_person(person: schemas.PersonShow, admin_id: UUID) -> schemas.PersonShow:
        with db_session:
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
            return schemas.PersonShow.from_orm(person_in_db)

    @staticmethod
    def get_all_persons(admin_id: UUID) -> list[schemas.PersonShow]:
        with db_session:
            try:
                persons = models.Person[admin_id].project_of_admin.persons
            except Exception as e:
                raise CustomError(f'Error: {e}')
            return [schemas.PersonShow.from_orm(p) for p in persons]

    @staticmethod
    @db_session
    def get_persons__from_plan_period(plan_period_id: UUID) -> list[schemas.PersonShow]:
        team_db = models.PlanPeriod.get_for_update(id=plan_period_id).team
        return [schemas.PersonShow.from_orm(p) for p in team_db.actors]

    @staticmethod
    def find_user_by_email(email: str) -> schemas.PersonShow | None:
        with db_session:
            person = models.Person.get(lambda p: p.email == email)
            if person:
                return schemas.PersonShow.from_orm(person)
            return None

    @staticmethod
    def set_new_actor_account_settings(person_id: UUID, new_email: EmailStr, new_password: str):
        with db_session:
            user = models.Person[person_id]
            hashed_psw = utils.hash_psw(new_password)
            user.set(email=new_email, password=hashed_psw)
            return schemas.Person.from_orm(user)

    @staticmethod
    def get_actors_in_dispatcher_teams(dispatcher_id: UUID) -> list[schemas.PersonShow]:
        with db_session:
            return [schemas.PersonShow.from_orm(p) for p in models.Person[dispatcher_id].teams_of_dispatcher.actors]


class Team:
    @staticmethod
    def update_team_from_project(team_id: UUID, new_team_name: str):
        with db_session:
            team_to_update = models.Team[team_id]
            team_to_update.name = new_team_name
            return schemas.Team.from_orm(team_to_update)

    @staticmethod
    def delete_team_from_project(team_id: UUID):
        with db_session:
            team_to_delete = models.Team[team_id]
            team_to_delete.delete()
            return schemas.Team.from_orm(team_to_delete)

    @staticmethod
    def get_all_project_teams(admin_id: UUID) -> list[schemas.Team]:
        with db_session:
            try:
                teams = models.Person[admin_id].project_of_admin.teams
            except Exception as e:
                raise CustomError(f'Error: {e}')
            return [schemas.Team.from_orm(t) for t in teams]

    @staticmethod
    def get_teams_of_dispatcher(dispatcher_id: UUID) -> list[schemas.Team]:
        with db_session:
            return [schemas.Team.from_orm(t) for t in models.Person[dispatcher_id].teams_of_dispatcher]

    @staticmethod
    def create_new_team(team: schemas.TeamCreate, person_id: str):
        person_id = UUID(person_id)
        with db_session:
            person = models.Person[person_id]
            new_team = models.Team(name=team.name, dispatcher=person)
            return schemas.TeamShow.from_orm(new_team)


class Project:
    @staticmethod
    def get_project_from_user_id(user_id) -> schemas.Project:
        with db_session:
            project = models.Person[user_id].project
            return schemas.Project.from_orm(project)

    @staticmethod
    def update_project_name(user_id: UUID, project_name: str):
        with db_session:
            project = models.Person[user_id].project_of_admin
            project.name = project_name
            return schemas.Project.from_orm(project)

    @staticmethod
    def create_account(project: schemas.ProjectCreate, person: schemas.PersonCreate):
        if not (password := person.password):
            password = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(password)
        with db_session:
            new_project = models.Project(name=project.name)
            new_person = models.Person(f_name=person.f_name, l_name=person.l_name, email=person.email,
                                       password=hashed_psw,
                                       project=new_project, project_of_admin=new_project)

            return {'admin': schemas.PersonShow.from_orm(new_person), 'password': password}

    @staticmethod
    def delete_a_account(project_id: UUID):
        with db_session:
            project_to_delete = models.Project[project_id]
            '''teams müssen vorab gelöscht werden, da in der Person-Entity im Feld "teams_of_dispatcher"
            cascade_delete wegen Sicherheitsgründen auf False gestellt ist.'''
            for team in project_to_delete.teams:
                team.delete()
            project_to_delete.delete()
            return schemas.Project.from_orm(project_to_delete)


class AvailDay:
    @staticmethod
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
        with db_session:
            for pp_id, dates in available_days.items():
                availables_in_db = models.Availables.get(lambda a:
                                                  a.person == models.Person[user_id] and a.plan_period == models.PlanPeriod[pp_id])
                if availables_in_db:
                    availables = availables_in_db
                    availables.avail_days.clear()
                else:
                    availables = models.Availables(plan_period=models.PlanPeriod[pp_id], person=models.Person[user_id])
                availables.notes = dates.pop('infos')

                av_days = {models.AvailDay(day=d, time_of_day=TimeOfDay(v), availables=availables)
                           for d, v in dates.items() if v != 'x'}
                plan_periods.append(schemas.PlanPeriod.from_orm(models.PlanPeriod[pp_id]))

        return plan_periods

    @staticmethod
    def get_avail_days_from_planperiod(planperiod_id: UUID) -> dict[UUID, dict[str, Union[str, schemas.AvailDay]]]:
        with db_session:
            availabless = list(models.PlanPeriod[planperiod_id].availabless)
            avail_days = {availables.person.id: {'notes': availables.notes,
                                                 'days': [schemas.AvailDay.from_orm(av_d) for av_d in
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
        return [schemas.AvailDayShow.from_orm(ad) for ad in availables.avail_days]


class PlanPeriod:
    @staticmethod
    def get_open_plan_periods(user_id: UUID) -> list[schemas.PlanPerEtFilledIn]:
        with db_session:
            person = models.Person.get(lambda p: p.id == user_id)
            actor_team = person.team_of_actor
            plan_periods = models.PlanPeriod.select(lambda pp: pp.team == actor_team and not pp.closed)

            plan_p_et_filled_in: list[schemas.PlanPerEtFilledIn] = []
            for pp in plan_periods:
                if not pp.availabless.select(lambda av: av.person == person):
                    filled_in = False
                else:
                    filled_in = True if list(pp.availabless.select(lambda av: av.person == person).first().avail_days) else False

                plan_p_et_filled_in.append(schemas.PlanPerEtFilledIn(plan_period=schemas.PlanPeriodShow.from_orm(pp),
                                                                     filled_in=filled_in))
                plan_p_et_filled_in.sort(key=lambda pp_e_fi: pp_e_fi.plan_period.start)
        return plan_p_et_filled_in

    @staticmethod
    def get_planperiods_last_recent_date(team_id: str) -> Optional[datetime.date]:
        with db_session:
            date = models.Team[UUID(team_id)].plan_periods.end
            if date:
                date = max(date)
            else:
                date = None
            return date

    @staticmethod
    def get_planperiods_of_team(team_id: UUID) -> list[schemas.PlanPeriod]:
        with db_session:
            planperiods = models.Team[team_id].plan_periods
            return [schemas.PlanPeriod.from_orm(pp) for pp in planperiods]

    @staticmethod
    def update_1_planperiod(planperiod: schemas.PlanPeriod) -> schemas.PlanPeriod:
        with db_session:
            planperiod_db = models.PlanPeriod[planperiod.id]

            planperiod_db.set(start=planperiod.start, end=planperiod.end, deadline=planperiod.deadline,
                              closed=planperiod.closed, notes=planperiod.notes)

            return schemas.PlanPeriod.from_orm(planperiod_db)

    @staticmethod
    def create_new_plan_period(team_id: str, date_start: datetime.date | None, date_end: datetime.date,
                               deadline: datetime.date, notes: str):
        with db_session:
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
            return schemas.PlanPeriod.from_orm(plan_period)

    @staticmethod
    def get_planperiod(pp_id: UUID) -> schemas.PlanPeriod:
        with db_session:
            return schemas.PlanPeriod.from_orm(models.PlanPeriod[pp_id])

    @staticmethod
    def delete_planperiod_from_team(planperiod_id: UUID):
        with db_session:
            planperiod_to_delete = models.PlanPeriod[planperiod_id]
            deleted_planperiod = schemas.PlanPeriod.from_orm(planperiod_to_delete)
            planperiod_to_delete.delete()
            return deleted_planperiod


class Availables:
    @staticmethod
    def get_not_feedbacked_availables(plan_period_id: str) -> list[schemas.Person]:
        with db_session:
            # persons_with_availables = list(PlanPeriod[UUID(plan_period_id)].availabless.person)
            # Bessere Alternative: alle Personen werden gelistet, die Einträge in Terminen oder Notes  gemacht haben,
            # anstatt alle Personen mit availables.
            persons_with_availables = list([availables.person for availables in models.PlanPeriod[UUID(plan_period_id)].availabless
                                            if (availables.notes or availables.avail_days)])
            persons_without_availables = [person for person in models.PlanPeriod[UUID(plan_period_id)].team.actors
                                          if person not in persons_with_availables]
            return [schemas.Person.from_orm(p) for p in persons_without_availables]


class APSchedulerJob:
    @staticmethod
    def get_scheduler_jobs() -> list[schemas.APSchedulerJob]:
        with db_session:
            jobs_db = models.APSchedulerJob.select()
            jobs = [schemas.APSchedulerJob.from_orm(job_db) for job_db in jobs_db]

            return jobs

    @staticmethod
    def add_job_to_db(job: apscheduler.job.Job):
        with db_session:
            print(f'add_job_to_db: {job=}')
            planperiod_db = models.PlanPeriod[UUID(job.id)]
            pickled_job = pickle.dumps(job)
            models.APSchedulerJob(plan_period=planperiod_db, job=pickled_job)

    @staticmethod
    def update_job_in_db(job: apscheduler.job.Job):
        with db_session:
            job_db = models.APSchedulerJob.get(lambda j: str(j.plan_period.id) == job.id)
            job_db.job = pickle.dumps(job)

    @staticmethod
    def delete_job_from_db(job_id: str):
        with db_session:
            plan_period_db = models.PlanPeriod.get(id=UUID(job_id))
            jobs_db_to_delete = models.APSchedulerJob.select(lambda asp: asp.plan_period == plan_period_db)
            for job_db_to_delete in jobs_db_to_delete:
                print(f'{job_db_to_delete=}')
                job_db_to_delete.delete()
            jobs_db_to_delete = [schemas.APSchedulerJob.from_orm(jd) for jd in jobs_db_to_delete]
            return jobs_db_to_delete


# todo: get_not_feedbacked_availables verbessern, sodass alle personen gelistet werden, die noch keine Einträge
#  in Terminen oder Notes gemacht haben.
