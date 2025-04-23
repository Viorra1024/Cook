import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chef_cook.settings')

app = Celery('chef_cook')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
