from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# Konfiguration mit timezone
scheduler = BackgroundScheduler({
    'apscheduler.job_defaults.max_instances': 2,
    'apscheduler.job_defaults.misfire_grace_time': 1200,
    'apscheduler.timezone': pytz.timezone('Europe/Berlin')  # Zeitzone für den Scheduler
})
