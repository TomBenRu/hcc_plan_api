import datetime
import pickle

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from pony.orm import Database, db_session, Required

db = Database()

app = FastAPI()

sched = BackgroundScheduler({'apscheduler.job_defaults.max_instances': 2,
                             'apscheduler.job_defaults.misfire_grace_time': 1200})

class Job(db.Entity):
    job_id = Required(str)
    job = Required(bytes)


db.bind(provider='sqlite', filename='jobs.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


def job1(job_id: str):
    print(f'job1: {datetime.datetime.now()}')
    with db_session:
        Job.get(lambda j: j.job_id == job_id).delete()


@app.on_event('startup')
def start_up():
    sched.start()
    with db_session:
        jobs_db = Job.select()
        for job_db in jobs_db:
            job = pickle.loads(job_db.job)
            sched.add_job(**job.__getstate__())
            print(f'Geladen: {job=}')


@app.post('/job')
def create_job(delta_time: int):
    run_date = datetime.datetime.now()+datetime.timedelta(seconds=delta_time)
    job = sched.add_job(job1, trigger='date', run_date=run_date, id=str(run_date), args=[str(run_date)])
    print(f'Erzeugt: {job.__getstate__()=}')
    pickled_job = pickle.dumps(job)
    with db_session:
        Job(job_id=str(run_date), job=pickled_job)


