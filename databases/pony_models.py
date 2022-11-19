from datetime import date
from datetime import datetime
from uuid import UUID
from pony.orm import Database, PrimaryKey, Required, Set, Optional, composite_key

from databases.enums import TimeOfDay


db_actors = Database()


class Project(db_actors.Entity):
    id = PrimaryKey(UUID, auto=True)
    name = Required(str, 50, unique=True)
    created_at = Required(date, default=lambda: date.today())
    last_modified = Required(datetime, precision=0, default=lambda: datetime.utcnow())
    persons = Set('Person', reverse='project')
    admin = Required('Person', reverse='admin_of_project')

    @property
    def teams(self):
        return self.persons.dispatcher_of_teams


class Person(db_actors.Entity):
    id = PrimaryKey(UUID, auto=True)
    f_name = Required(str, 50)
    l_name = Required(str, 50)
    email = Required(str, 50, unique=True)
    password = Required(str)
    created_at = Required(date, default=lambda: date.today())
    last_modified = Required(datetime, default=lambda: datetime.utcnow())
    project = Required(Project, reverse='persons')
    admin_of_project = Optional(Project, reverse='admin')
    dispatcher_of_teams = Set('Team', reverse='dispatcher')
    actor_of_team = Optional('Team', reverse='actors')
    availables = Set('Availables')

    composite_key(f_name, l_name, project)


class Team(db_actors.Entity):
    id = PrimaryKey(UUID, auto=True)
    name = Required(str, 50, unique=True)
    created_at = Required(date, default=lambda: date.today())
    last_modified = Required(datetime, default=lambda: datetime.utcnow())
    actors = Set(Person, reverse='actor_of_team')
    dispatcher = Required(Person, reverse='dispatcher_of_teams')
    plan_periods = Set('PlanPeriod')

    @property
    def project(self):
        return self.dispatcher.project


class Availables(db_actors.Entity):
    id = PrimaryKey(UUID, auto=True)
    notes = Optional(str)
    created_at = Required(date, default=lambda: date.today())
    last_modified = Required(datetime, default=lambda: datetime.utcnow())
    plan_period = Required('PlanPeriod')
    person = Required(Person)
    avail_days = Set('AvailDay')

    def before_update(self):
        self.last_modified = datetime.utcnow()


class PlanPeriod(db_actors.Entity):
    id = PrimaryKey(UUID, auto=True)
    start = Required(date)
    end = Required(date)
    deadline = Required(date)
    notes = Optional(str)
    closed = Required(bool, default=False)
    created_at = Required(date, default=lambda: date.today())
    last_modified = Required(datetime, default=lambda: datetime.utcnow())
    team = Required(Team)
    availabless = Set(Availables)

    @property
    def dispatcher(self):
        return self.team.dispatcher


class AvailDay(db_actors.Entity):
    id = PrimaryKey(UUID, auto=True)
    day = Required(date)
    created_at = Required(date, default=lambda: date.today())
    last_modified = Required(datetime, default=lambda: datetime.utcnow())
    time_of_day = Required(TimeOfDay)
    availables = Required(Availables)

    def before_update(self):
        self.last_modified = datetime.utcnow()
