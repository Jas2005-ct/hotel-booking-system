from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_files.settings')
app = Celery('project_files')
app.conf.enable_utc = False

app.conf.update(
    timezone = 'Asia/Kolkata'
)

app.conf.beat_schedule = {
    'send-reminder-emails': {
        'task': 'table_reservation.tasks.reminder_before_one_hour',
        'schedule': crontab(minute='*'),
    },
    'table_status_check':{
        'task': 'table_reservation.tasks.change_table_status',
        'schedule': crontab(minute='*'),
    }
}




app.config_from_object(settings,namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request}')
    