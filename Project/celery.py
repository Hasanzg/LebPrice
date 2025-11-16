import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')

app = Celery('Project')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat schedule (for periodic tasks)
app.conf.beat_schedule = {
    'scrape-all-stores-every-6-hours': {
        'task': 'products.tasks.scrape_all_stores',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')