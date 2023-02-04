import pickle
from datetime import date, datetime, timedelta
from typing import Optional, Set, Any, List, Union
from uuid import UUID

import apscheduler.job
from pydantic import BaseModel, Field, EmailStr, conint, validator
from .enums import TimeOfDay


class ProjectCreate(BaseModel):
    name: str
    # admin: Optional['Person']

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
    project: Project


class PersonShow(Person):
    project_of_admin: Optional[Project]
    teams_of_dispatcher: List['Team']
    team_of_actor: Optional['Team']

    @validator('teams_of_dispatcher', pre=True, allow_reuse=True)
    def pony_set_to_list(cls, values):
        return [v for v in values]


class TeamCreate(BaseModel):
    name: str
    dispatcher: Optional[Person]

    class Config:
        orm_mode = True


class Team(TeamCreate):
    id: UUID
    dispatcher: Person


class TeamShow(Team):
    pass


class AvailablesCreate(BaseModel):
    person: Person
    notes: str

    class Config:
        orm_mode = True


class Availables(AvailablesCreate):
    id: UUID


class AvailablesShow(Availables):
    plan_period: 'PlanPeriod'
    avail_days: List['AvailDay']

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
    availabless: List[AvailablesShow]

    def avail_days(self, actor_id: int) -> dict[date, Any]:
        av_days = {}
        for available in self.availabless:
            if available.person.id != actor_id:
                continue
            for av_d in available.avail_days:
                av_days[av_d.day] = av_d.time_of_day.value
        return av_days

    def notes_of_availables(self, actor_id: int) -> str:
        for avail in self.availabless:
            if avail.person.id == actor_id:
                return avail.notes
        return ''

    @property
    def all_days(self):
        delta: timedelta = self.end - self.start
        all_days: List[datetime.date] = []
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
    plan_period: PlanPeriodShow
    filled_in: bool


class AvailDayCreate(BaseModel):
    day: date
    time_of_day: TimeOfDay

    class Config:
        orm_mode = True


class AvailDay(AvailDayCreate):
    id: UUID
    created_at: date
    last_modified: datetime
    time_of_day: TimeOfDay
    # availables: Availables


class AvailDayShow(AvailDay):
    pass


# --------------------------------------------------------------------------------------


class RemainderDeadlineCreate(BaseModel):
    plan_period: PlanPeriod
    trigger: Optional[str]
    run_date: datetime
    func: Optional[str]
    args: List = []

    class Config:
        orm_mode = True


class APSchedulerJob(BaseModel):
    plan_period: PlanPeriod
    job: apscheduler.job.Job

    @validator('job', pre=True, allow_reuse=True)
    def pickled_job_to_job(cls, pickled_job):
        return pickle.loads(pickled_job)

    class Config:
        orm_mode = True


# --------------------------------------------------------------------------------------


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Union[UUID, str, None] = None
    authorizations: List[str]


ProjectCreate.update_forward_refs(**locals())
Project.update_forward_refs(**locals())
PersonShow.update_forward_refs(**locals())
PersonCreate.update_forward_refs(**locals())
AvailablesShow.update_forward_refs(**locals())
TeamShow.update_forward_refs(**locals())
