from datetime import date, datetime, timedelta
from typing import Optional, Set, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, conint, validator
from .enums import TimeOfDay


class ProjectCreate(BaseModel):
    name: str
    admin: Optional['Person']

    class Config:
        orm_mode = True


class Project(ProjectCreate):
    id: UUID


class ProjectShow(Project):
    pass


class PersonCreate(BaseModel):
    f_name: str
    l_name: str
    email: EmailStr
    password: Optional[str]
    project: Optional[Project]

    class Config:
        orm_mode = True


class Person(PersonCreate):
    id: UUID


class PersonShow(Person):
    admin_of_project: Optional[Project]
    dispatcher_of_teams = list['Team']
    actor_of_team = Optional['Team']

    @validator('dispatcher_of_teams', pre=True, allow_reuse=True)
    def pony_set_to_list(cls, values):
        return [v for v in values]


class TeamCreate(BaseModel):
    name: str
    dipatcher: Person

    class Config:
        orm_mode = True


class Team(TeamCreate):
    id: UUID


class TeamShow(Team):
    pass


class AvailablesCreate(BaseModel):
    planperiod: 'PlanPeriod'
    person: Person
    notes: str

    class Config:
        orm_mode = True


class Availables(AvailablesCreate):
    id: UUID


class AvailablesShow(Availables):
    avail_days: list['AvailDay']

    @validator('avail_days', pre=True, allow_reuse=True)
    def pony_set_to_list(cls, values):
        return [v for v in values]


class PlanPeriodCreate(BaseModel):
    start: date
    end: date
    deadline: date
    notes: Optional[str]
    team: Team

    class Config:
        orm_mode = True


class PlanPeriod(PlanPeriodCreate):
    id: UUID
    closed: bool


class PlanPeriodShow(PlanPeriod):
    availabless: list[Availables]

    @property
    def all_days(self):
        delta: timedelta = self.end - self.start
        all_days: list[datetime.date] = []
        for i in range(delta.days + 1):
            day = self.start + timedelta(days=i)
            all_days.append(day)
        return all_days

    @property
    def calender_week_days(self):
        kw__day_wd = {d.isocalendar()[1]: [] for d in self.all_days}
        for day in self.all_days:
            kw__day_wd[day.isocalendar()[1]].append((day, date.weekday(day)))
        return kw__day_wd

    @validator('availabless', pre=True, allow_reuse=True)
    def pony_set_to_list(cls, values):
        return [v for v in values]


class PlanPerEtFilledIn(BaseModel):
    plan_period: PlanPeriod
    filled_in: bool


class AvailDayCreate(BaseModel):
    day: date
    time_of_day: TimeOfDay

    class Config:
        orm_mode = True


class AvailDay(AvailDayCreate):
    id: UUID


class AvailDayShow(AvailDay):
    pass


# --------------------------------------------------------------------------------------


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[UUID] = None
    authorization: Optional[str]


AvailablesShow.update_forward_refs(**locals())
TeamShow.update_forward_refs(**locals())
ProjectCreate.update_forward_refs(**locals())
PersonShow.update_forward_refs(**locals())
PersonCreate.update_forward_refs(**locals())
