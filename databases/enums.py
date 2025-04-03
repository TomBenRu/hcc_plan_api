from enum import Enum


class TimeOfDay(Enum):
    morning = 'v'
    afternoon = 'n'
    whole_day = 'g'
    evening = 'a'


class AuthorizationTypes(Enum):
    supervisor = 'supervisor'
    admin = 'admin'
    dispatcher = 'dispatcher'
    actor = 'actor'
    google_calendar = 'google_calendar'
