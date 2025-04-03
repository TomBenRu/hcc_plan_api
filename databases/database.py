from enum import Enum

from pony.orm import Database, sql_debug

import settings
from databases import models
from .enum_converter import EnumConverter


# zum Deployen müssen server_remote_access, local und from_outside False sein
# zum lokalen Testen mit lokaler Datenbank muss local True sein, frm_outside und server_remote_access False sein
server_remote_access = False
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


def start_db():
    if not server_remote_access:
        for db, file in ((models.db_actors, settings.settings.db_actors), ):
            generate_db_mappings(db=db, file=file)
