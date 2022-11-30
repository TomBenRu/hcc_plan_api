from enum import Enum

from pony.orm import Database, sql_debug

# the models have to be imported for correct database mapping
from .pony_models import (db_actors, Team, Person, PlanPeriod, Availables, AvailDay, Project)

import settings
from .enum_converter import EnumConverter


# zum Deployen müssen server_remote_access, local und from_outside False sein
server_remote_acces = False
local = False  # True: sqlite-database, False: postgresql-database
from_outside = False  # False: calling database from same API

# sql_debug(True)


def generate_db_mappings(db: Database, file: str):
    if not local:
        #########################################################################################################
        # this ist the connection to postgresql on render.com
        if from_outside:
            host = settings.settings.host_sql + '.frankfurt-postgres.render.com'
        else:
            host = settings.settings.host_sql
        db.bind(provider=settings.settings.provider_sql, user=settings.settings.user_sql,
                password=settings.settings.password_sql, host=host, database=settings.settings.database_sql)
        ##########################################################################################################
    else:
        provider = settings.settings.provider

        db.bind(provider=provider, filename=file, create_db=True)

    # Register the type converter with the database
    db.provider.converter_classes.append((Enum, EnumConverter))

    db.generate_mapping(create_tables=True)


if not server_remote_acces:
    for db, file in ((db_actors, settings.settings.db_actors), ):
        generate_db_mappings(db=db, file=file)

if __name__ == '__main__':
    pass
