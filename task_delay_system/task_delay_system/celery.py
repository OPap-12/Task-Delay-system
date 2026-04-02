import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')

app = Celery('task_delay_system')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'daily-manager-digest': {
        'task': 'tasks.tasks.send_manager_daily_digest',
        'schedule': crontab(hour=8, minute=0),  # 8:00 AM every day
    },
    'hourly-employee-reminders': {
        'task': 'tasks.tasks.send_employee_reminders',
        'schedule': crontab(minute=0),  # Every hour
    },
}
