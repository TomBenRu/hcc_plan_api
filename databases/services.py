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
import pydantic_models as pm


class CustomError(Exception):
    pass


def create_person(admin_id: UUID, person: pm.PersonCreateRemote):
    with db_session:
        project = Person[admin_id].project
        if select(p for p in project.persons if p.email == person.email):
            raise CustomError(f'Eine Person mit Email {person.email} ist schon vorhanden.')
        if select(p for p in project.persons if p.f_name == person.f_name and p.l_name == person.l_name):
            raise CustomError(f'Eine Person mit Namen "{person.f_name} {person.l_name}" ist schon vorhanden.')
        person.project = project
        new_person = Person(**person.dict())
        return PersonShowBase.from_orm(new_person)


def get_project_from_user_id(user_id) -> pm.Project:
    with db_session:
        project = Person[user_id].project
        return pm.Project.from_orm(project)


def get_all_persons(admin_id: UUID) -> list[pm.Person]:
    with db_session:
        try:
            persons = Person[admin_id].admin_of_project.persons
        except Exception as e:
            raise CustomError(f'Error: {e}')
        return [pm.Person.from_orm(p) for p in persons]


def get_all_project_teams(admin_id: UUID) -> list[pm.Team]:
    with db_session:
        try:
            teams = Person[admin_id].admin_of_project.teams
        except Exception as e:
            raise CustomError(f'Error: {e}')
        return [pm.Team.from_orm(t) for t in teams]


def save_new_actor(user: ActorCreateBase):
    hashed_psw = utils.hash_psw(user.password)
    user.password = hashed_psw

    with db_session:
        try:
            team = Team.get(lambda t: t.name == user.team.name)
            print(team)
            person = Person(**user.person.dict())
            user_in_db = Actor(password=user.password, person=person, team=team)
        except Exception as e:
            raise ValueError(e)
    return user_in_db


def find_user_by_email(email: str, authorization: AuthorizationTypes) -> pm.PersonShow | None:
    with db_session:
        person = Person.get(lambda p: p.email == email)
        if person:
            if authorization == AuthorizationTypes.actor:
                if person.actor_of_team:
                    return pm.PersonShow.from_orm(person)
            if authorization == AuthorizationTypes.admin:
                if person.admin_of_project:
                    return pm.PersonShow.from_orm(person)
            if authorization == AuthorizationTypes.dispatcher:
                if person.dispatcher_of_teams.select():
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
        actor_team = person.actor_of_team
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


def get_plan_periods_from_ids(planperiods: list[int]):
    with db_session:
        plan_periods = [PlanPeriodBase.from_orm(PlanPeriod[i]) for i in planperiods]
    return plan_periods


def get_past_plan_periods(team_id: str, nbr_past_planperiods: int, only_not_closed: bool = False):
    """nbr_past_planperiods: positiver Wert -> Anzahl zurückliegender Planperioden.
       0 -> alle Planperioden"""
    with db_session:
        planperiods: list = list(PlanPeriodBase.from_orm(pp) for pp in Team[UUID(team_id)].plan_periods)
        return planperiods


def get_planperiods_last_recent_date(team_id: str) -> datetime.date:
    with db_session:
        date = Team[UUID(team_id)].plan_periods.end
        if date:
            date = max(date)
        else:
            date = datetime.date(1980, 1, 1)
        return date


def get_all_actors():
    with db_session:
        actors = [ActorBase.from_orm(a) for a in Actor.select()]
    return actors


def get_user_by_id(user_id: UUID) -> pm.Person:
    with db_session:
        person = Person[user_id]
        return pm.Person.from_orm(person)


def get_actors_in_dispatcher_teams(dispatcher_id: str):
    with db_session:
        return [{'f_name': actor.f_name, 'l_name': actor.l_name, 'id': actor.id}
                for actor in Dispatcher[dispatcher_id].teams.actors]


def get_avail_days_from_actor(actor_id: str):
    actor_id = UUID(actor_id)
    with db_session:
        all_avail_days = {}
        for availables in Actor[actor_id].availables.select():
            if availables.plan_period.closed:
                continue
            all_avail_days[availables.id] = {'start': availables.plan_period.start, 'end': availables.plan_period.end}
            notes = availables.notes
            all_avail_days[availables.id]['notes'] = notes
            avail_days = availables.avail_days.select()
            all_avail_days[availables.id]['avail_days'] = [AvailDayBase.from_orm(ad) for ad in avail_days]
        return all_avail_days


def create_new_team(team: pm.TeamCreate):
    with db_session:
        new_team = Team(**team.dict())
        return pm.TeamShow.from_orm(new_team)


def create_admin(project: ProjectBase, person: PersonCreateRemoteBase):  # aktuell
    password = secrets.token_urlsafe(8)
    hashed_psw = utils.hash_psw(password)
    with db_session:
        if proj := Project.get(lambda pr: pr.name == project.name):
            raise ValueError('Es gibt bereits ein Projekt dieses Namens.')
        new_project = Project(name=project.name)
        if pers := Person.get(lambda p: p.email == person.email):
            if pers.f_name != person.f_name or pers.l_name != person.l_name:
                raise ValueError('Es gibt bereits eine Person mit dieser Email.')
            else:
                person = PersonBase.from_orm(pers)

        person = Person(f_name=person.f_name, l_name=person.l_name, email=person.email, project=new_project)
        new_admin = Admin(password=hashed_psw, person=person)
        new_admin.to_dict()
        return AdminShowBase.from_orm(new_admin), password


def create_actor__remote(person: PersonCreateRemoteBase, team_id: str):  # aktuell
    with db_session:
        team_db = Team[team_id]
        if Actor.get(lambda a: a.email == person.email and a.team.project == team_db.project):
            raise CustomError("Es ist schon ein Mitarbeiter mit dieser Email vorhanden.")
        if pers := Person.get(lambda p: p.email == person.email and p.project == team_db.project):
            if pers.f_name != person.f_name or pers.l_name != person.l_name:
                raise CustomError('Es gibt bereits eine Person mit dieser Email, '
                                  'aber die sonstigen Personendaten stimmen nicht überein.')
            else:
                person_db = pers
        else:
            person.project = team_db.project
            person_db = Person(**person.dict())
        password = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(password)
        new_actor = Actor(person=person_db, team=team_db, password=hashed_psw)
        return {'actor': ActorShowBase.from_orm(new_actor), 'password': password}


def get_teams_of_dispatcher(dispatcher_id: UUID):
    with db_session:
        teams = Dispatcher[dispatcher_id].teams.select()
        return [TeamShowBase.from_orm(t) for t in teams]


def get_team_by_name(name: str) -> TeamBase:
    with db_session:
        team = Team.get(lambda t: t.name == name)
        if not team:
            raise KeyError({'detail': f'Kein Team mit Namen: {name}'})
        return TeamBase.from_orm(team)


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
        return PlanPeriodBase.from_orm(plan_period)


def change_status_planperiod(plan_period_id: int, closed: bool, dispatcher_id: int):
    with db_session:
        try:
            plan_period = PlanPeriod[plan_period_id]
        except Exception as e:
            raise KeyError(f'Die Planperiode mit ID: {plan_period_id} ist nicht vorhanden')
        if Dispatcher[dispatcher_id] not in PlanPeriod[plan_period_id].dispatchers:
            raise KeyError(f'Die Planperiode mit ID: {plan_period_id} ist nicht vorhanden.')
        plan_period.closed = closed
        return PlanPeriodBase.from_orm(plan_period)


if __name__ == '__main__':
    pass
