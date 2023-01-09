import datetime
import secrets
import time
from typing import Type, Optional
from uuid import UUID

from pony.orm import Database, db_session, select, TransactionIntegrityError
from pony.orm.core import Multiset, flush, commit
from pydantic import EmailStr

from utilities import utils
from .database import (Team, Person, PlanPeriod, Availables, AvailDay, Project)
from .enums import TimeOfDay, AuthorizationTypes
import databases.pydantic_models as pm


class CustomError(Exception):
    pass


def create_person(admin_id: UUID, person: pm.PersonCreate):
    if not (password := person.password):
        password = secrets.token_urlsafe(8)
    hashed_psw = utils.hash_psw(password)
    with db_session:
        project = Person[admin_id].project
        person.project = project
        person.password = hashed_psw
        new_person = Person(**person.dict())
        return {'person': pm.PersonShow.from_orm(new_person), 'password': password}


def set_new_password(user_id: UUID):
    new_psw = secrets.token_urlsafe(8)
    hashed_psw = utils.hash_psw(new_psw)
    with db_session:
        person_db = Person[user_id]
        person_db.password = hashed_psw
        return pm.Person.from_orm(person_db), new_psw


def delete_person_from_project(person_id: UUID):
    with db_session:
        person_to_delete = Person[person_id]
        person_to_delete.delete()
        return pm.Person.from_orm(person_to_delete)


def update_team_from_project(team_id: UUID, new_team_name: str):
    with db_session:
        team_to_update = Team[team_id]
        team_to_update.name = new_team_name
        return pm.Team.from_orm(team_to_update)


def delete_team_from_project(team_id: UUID):
    with db_session:
        team_to_delete = Team[team_id]
        team_to_delete.delete()
        return pm.Team.from_orm(team_to_delete)


def make_person__actor_of_team(person: pm.Person, team: pm.Team, user_id: UUID):
    with db_session:
        dispatcher = Person[user_id]
        if dispatcher.project.id != person.project.id or (team.id not in dispatcher.teams.id):
            raise CustomError('Person ist nicht im Projekt oder Dispatcher ist nich für das Team zuständig.')
        Team[team.id].dispatcher = Person[person.id]
        return pm.PersonShow.from_orm(person)


def update_person(person: pm.PersonShow, admin_id: UUID) -> pm.PersonShow:
    with db_session:
        project = Person[admin_id].project
        person_in_db = Person.get_for_update(id=person.id)
        if person.project_of_admin:
            project.admin = person_in_db
        for t in person.teams_of_dispatcher:
            Team[t.id].dispatcher = person_in_db
        if person.team_of_actor:
            person_in_db.team_of_actor = Team[person.team_of_actor.id]
        else:
            person_in_db.team_of_actor = None
        return pm.PersonShow.from_orm(person_in_db)


def get_project_from_user_id(user_id) -> pm.Project:
    with db_session:
        project = Person[user_id].project
        return pm.Project.from_orm(project)


def update_project_name(user_id: UUID, project_name: str):
    with db_session:
        project = Person[user_id].project_of_admin
        project.name = project_name
        return pm.Project.from_orm(project)


def get_all_persons(admin_id: UUID) -> list[pm.PersonShow]:
    with db_session:
        try:
            persons = Person[admin_id].project_of_admin.persons
        except Exception as e:
            raise CustomError(f'Error: {e}')
        return [pm.PersonShow.from_orm(p) for p in persons]


def get_all_project_teams(admin_id: UUID) -> list[pm.Team]:
    with db_session:
        try:
            teams = Person[admin_id].project_of_admin.teams
        except Exception as e:
            raise CustomError(f'Error: {e}')
        return [pm.Team.from_orm(t) for t in teams]


def get_list_of_authorizations(person: pm.PersonShow) -> list[AuthorizationTypes]:
    auth_types = []
    if person.team_of_actor:
        auth_types.append(AuthorizationTypes.actor)
    if person.project_of_admin:
        auth_types.append(AuthorizationTypes.admin)
    if person.teams_of_dispatcher:
        auth_types.append(AuthorizationTypes.dispatcher)
    return auth_types


def find_user_by_email(email: str) -> pm.PersonShow | None:
    with db_session:
        person = Person.get(lambda p: p.email == email)
        if person:
            return pm.PersonShow.from_orm(person)
        return None


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
            availables_in_db = Availables.get(lambda a:
                                              a.person == Person[user_id] and a.plan_period == PlanPeriod[pp_id])
            if availables_in_db:
                availables = availables_in_db
                availables.avail_days.clear()
            else:
                availables = Availables(plan_period=PlanPeriod[pp_id], person=Person[user_id])
            availables.notes = dates.pop('infos')

            av_days = {AvailDay(day=d, time_of_day=TimeOfDay(v), availables=availables)
                       for d, v in dates.items() if v != 'x'}
            plan_periods.append(pm.PlanPeriod.from_orm(PlanPeriod[pp_id]))

    return plan_periods


def get_open_plan_periods(user_id: UUID) -> list[pm.PlanPerEtFilledIn]:
    with db_session:
        person = Person.get(lambda p: p.id == user_id)
        actor_team = person.team_of_actor
        plan_periods = PlanPeriod.select(lambda pp: pp.team == actor_team and not pp.closed)

        plan_p_et_filled_in: list[pm.PlanPerEtFilledIn] = []
        for pp in plan_periods:
            if not pp.availabless.select(lambda av: av.person == person):
                filled_in = False
            else:
                filled_in = True if list(pp.availabless.select(lambda av: av.person == person).first().avail_days) else False

            plan_p_et_filled_in.append(pm.PlanPerEtFilledIn(plan_period=pm.PlanPeriodShow.from_orm(pp),
                                                            filled_in=filled_in))
    return plan_p_et_filled_in


def set_new_actor_account_settings(person_id: UUID, new_email: EmailStr, new_password: str):
    with db_session:
        user = Person[person_id]
        hashed_psw = utils.hash_psw(new_password)
        user.set(email=new_email, password=hashed_psw)
        return pm.Person.from_orm(user)


def get_teams_of_dispatcher(dispatcher_id: UUID) -> list[pm.Team]:
    with db_session:
        return [pm.Team.from_orm(t) for t in Person[dispatcher_id].teams_of_dispatcher]


def get_planperiods_last_recent_date(team_id: str) -> Optional[datetime.date]:
    with db_session:
        date = Team[UUID(team_id)].plan_periods.end
        if date:
            date = max(date)
        else:
            date = None
        return date


def get_planperiods_of_team(team_id: UUID) -> list[pm.PlanPeriod]:
    with db_session:
        planperiods = Team[team_id].plan_periods
        return [pm.PlanPeriod.from_orm(pp) for pp in planperiods]


def update_1_planperiod(planperiod: pm.PlanPeriod) -> pm.PlanPeriod:
    with db_session:
        planperiod_db = PlanPeriod[planperiod.id]

        planperiod_db.set(start=planperiod.start, end=planperiod.end, deadline=planperiod.deadline,
                          closed=planperiod.closed, notes=planperiod.notes)

        return pm.PlanPeriod.from_orm(planperiod_db)


def get_user_by_id(user_id: UUID) -> pm.Person:
    with db_session:
        person = Person[user_id]
        return pm.Person.from_orm(person)


def get_actors_in_dispatcher_teams(dispatcher_id: UUID) -> list[pm.PersonShow]:
    with db_session:
        return [pm.PersonShow.from_orm(p) for p in Person[dispatcher_id].teams_of_dispatcher.actors]


def get_avail_days_from_planperiod(planperiod_id: UUID) -> dict[UUID, list[pm.AvailDay]]:
    with db_session:
        availabless = list(PlanPeriod[planperiod_id].availabless)
        avail_days = {availables.person.id: [pm.AvailDay.from_orm(av_d) for av_d in list(availables.avail_days)]
                      for availables in availabless}
        return avail_days


def create_new_team(team: pm.TeamCreate, person_id: str):
    person_id = UUID(person_id)
    with db_session:
        person = Person[person_id]
        new_team = Team(name=team.name, dispatcher=person)
        return pm.TeamShow.from_orm(new_team)


def create_account(project: pm.ProjectCreate, person: pm.PersonCreate):
    if not (password := person.password):
        password = secrets.token_urlsafe(8)
    hashed_psw = utils.hash_psw(password)
    with db_session:
        new_project = Project(name=project.name)
        new_person = Person(f_name=person.f_name, l_name=person.l_name, email=person.email, password=hashed_psw,
                            project=new_project, project_of_admin=new_project)

        return {'admin': pm.PersonShow.from_orm(new_person), 'password': password}


def delete_a_account(project_id: UUID):
    with db_session:
        project_to_delete = Project[project_id]
        '''teams müssen vorab gelöscht werden, da in der Person-Entity im Feld "teams_of_dispatcher"
        cascade_delete wegen Sicherheitsgründen auf False gestellt ist.'''
        for team in project_to_delete.teams:
            team.delete()
        project_to_delete.delete()
        return pm.Project.from_orm(project_to_delete)


def create_new_plan_period(team_id: str, date_start: datetime.date | None, date_end: datetime.date,
                           deadline: datetime.date, notes: str):
    with db_session:
        max_date: datetime.date | None = None
        if planperiods := PlanPeriod.select(lambda pp: pp.team.id == UUID(team_id)):
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

        plan_period = PlanPeriod(start=date_start, end=date_end, deadline=deadline, notes=notes,
                                 team=Team.get(lambda t: t.id == UUID(team_id)))
        return pm.PlanPeriod.from_orm(plan_period)


def delete_planperiod_from_team(planperiod_id: UUID):
    with db_session:
        planperiod_to_delete = PlanPeriod[planperiod_id]
        deleted_planperiod = pm.PlanPeriod.from_orm(planperiod_to_delete)
        planperiod_to_delete.delete()
        return deleted_planperiod


def change_status_planperiod(plan_period_id: int, closed: bool, dispatcher_id: int):
    pass


if __name__ == '__main__':
    pass
