import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery 6.0+ will change retry semantics; enable retries explicitly now.
app.conf.broker_connection_retry_on_startup = True

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Celery Beat Schedule
app.conf.beat_schedule = {
    'check-campaign-status-every-5-minutes': {
        'task': 'apps.campaigns.tasks.check_campaign_status',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'process-email-events-every-minute': {
        'task': 'apps.campaigns.tasks.process_email_events',
        'schedule': crontab(minute='*'),  # Every minute
    },
    'cleanup-old-logs-daily': {
        'task': 'apps.campaigns.tasks.cleanup_old_logs',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}
