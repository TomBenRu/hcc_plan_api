import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from databases.services import get_scheduler_jobs
from routers import auth, actors, supervisor, admin, dispatcher, index
from utilities.scheduler import scheduler
from utilities.send_mail import probe_job
import databases.pydantic_models as pm

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')


@app.on_event('startup')
def scheduler_startup():
    scheduler.start()
    print('scheduler started')
    jobs: list[pm.RemainderDeadline] = get_scheduler_jobs()
    print(f'{[(j.plan_period.id, j.run_date) for j in jobs]}')
    for job in jobs:
        scheduler.add_job(func=probe_job, trigger=job.trigger, run_date=job.run_date, id=str(job.plan_period.id),
                          args=job.args)


app.include_router(index.router)

app.include_router(auth.router)

app.include_router(actors.router)

app.include_router(admin.router)

app.include_router(supervisor.router)

app.include_router(dispatcher.router)


if __name__ == '__main__':
    uvicorn.run(app)
    import databases.database