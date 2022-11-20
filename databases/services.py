import datetime
import secrets
import time
from typing import Type
from uuid import UUID

from pony.orm import Database, db_session, select, TransactionIntegrityError
from pony.orm.core import Multiset

from utilities import utils
from .database import (Team, Person, PlanPeriod, Availables, AvailDay, Project)
from .enums import TimeOfDay, AuthorizationTypes
import databases.pydantic_models as pm


class CustomError(Exception):
    pass


def create_person(admin_id: UUID, person: pm.PersonCreate):
    with db_session:
        project = Person[admin_id].project
        person.project = project
        new_person = Person(**person.dict())
        return pm.PersonShow.from_orm(new_person)


def make_person__actor_of_team(person: pm.Person, team: pm.Team, user_id: UUID):
    with db_session:
        dispatcher = Person[user_id]
        if dispatcher.project.id != person.project.id or (team.id not in dispatcher.teams.id):
            raise CustomError('Person ist nicht im Projekt oder Dispatcher ist nich für das Team zuständig.')
        Team[team.id].dispatcher = Person[person.id]
        return pm.PersonShow.from_orm(person)


def get_project_from_user_id(user_id) -> pm.Project:
    with db_session:
        project = Person[user_id].project
        return pm.Project.from_orm(project)


def get_all_persons(admin_id: UUID) -> list[pm.Person]:
    with db_session:
        try:
            persons = Person[admin_id].project_of_admin.persons
        except Exception as e:
            raise CustomError(f'Error: {e}')
        return [pm.Person.from_orm(p) for p in persons]


def get_all_project_teams(admin_id: UUID) -> list[pm.Team]:
    with db_session:
        try:
            teams = Person[admin_id].project_of_admin.teams
        except Exception as e:
            raise CustomError(f'Error: {e}')
        return [pm.Team.from_orm(t) for t in teams]


def find_user_by_email(email: str, authorization: AuthorizationTypes) -> pm.PersonShow | None:
    with db_session:
        person = Person.get(lambda p: p.email == email)
        if person:
            if authorization == AuthorizationTypes.actor:
                if person.team_of_actor:
                    return pm.PersonShow.from_orm(person)
            if authorization == AuthorizationTypes.admin:
                if person.project_of_admin:
                    return pm.PersonShow.from_orm(person)
            if authorization == AuthorizationTypes.dispatcher:
                if person.teams_of_dispatcher.select():
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
            plan_p_et_filled_in.append(pm.PlanPerEtFilledIn(plan_period=pm.PlanPeriod.from_orm(pp),
                                                            filled_in=filled_in))
    return plan_p_et_filled_in


def get_teams_of_dispatcher(dispatcher_id: UUID) -> list[pm.Team]:
    with db_session:
        return [pm.Team.from_orm(t) for t in Person[dispatcher_id].teams_of_dispatcher]


def get_planperiods_last_recent_date(team_id: str) -> datetime.date:
    with db_session:
        date = Team[UUID(team_id)].plan_periods.end
        if date:
            date = max(date)
        else:
            date = datetime.date(1980, 1, 1)
        return date


def get_user_by_id(user_id: UUID) -> pm.Person:
    with db_session:
        person = Person[user_id]
        return pm.Person.from_orm(person)


def get_actors_in_dispatcher_teams(dispatcher_id: UUID) -> list[pm.Person]:
    with db_session:
        return [pm.Person.from_orm(p) for p in Person[dispatcher_id].teams_of_dispatcher.actors]


def get_avail_days_from_actor(actor_id: UUID):
    with db_session:
        all_avail_days = {}
        for availables in Person[actor_id].availabless.select():
            if availables.plan_period.closed:
                continue
            all_avail_days[availables.id] = {'start': availables.plan_period.start, 'end': availables.plan_period.end}
            notes = availables.notes
            all_avail_days[availables.id]['notes'] = notes
            avail_days = availables.avail_days.select()
            all_avail_days[availables.id]['avail_days'] = [pm.AvailDay.from_orm(ad) for ad in avail_days]
        return all_avail_days


def create_new_team(team: pm.TeamCreate):
    with db_session:
        new_team = Team(**team.dict())
        return pm.TeamShow.from_orm(new_team)


def create_account(project: pm.ProjectCreate, person: pm.PersonCreate):  # aktuell
    password = secrets.token_urlsafe(8)
    hashed_psw = utils.hash_psw(password)
    with db_session:
        new_project = Project(name=project.name)
        new_person = Person(**person.dict())
        new_person.project = new_project

        return pm.ProjectShow.from_orm(new_project)


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


def change_status_planperiod(plan_period_id: int, closed: bool, dispatcher_id: int):
    pass


if __name__ == '__main__':
    pass
