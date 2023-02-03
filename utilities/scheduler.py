from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler({'apscheduler.job_defaults.max_instances': 2,
                                 'apscheduler.job_defaults.misfire_grace_time': 1200})
