from uuid import UUID

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every

from databases.services import get_actors_in_dispatcher_teams, get_not_feedbacked_availables
from routers import auth, actors, supervisor, admin, dispatcher, index

app = FastAPI()


@app.on_event('startup')
@repeat_every(seconds=2, wait_first=True)
def remainder_availables():
    print('remainder')
    actors = get_actors_in_dispatcher_teams(UUID('80ea7175-497b-40bb-9b4d-3ffc78bb0bd2'))
    for person in actors:
        not_feedbacked = get_not_feedbacked_availables(person)
        print(f'{person.f_name=}, {not_feedbacked=}')


app.mount('/static', StaticFiles(directory='static'), name='static')


app.include_router(index.router)

app.include_router(auth.router)

app.include_router(actors.router)

app.include_router(admin.router)

app.include_router(supervisor.router)

app.include_router(dispatcher.router)


if __name__ == '__main__':
    uvicorn.run(app)
    import databases.database