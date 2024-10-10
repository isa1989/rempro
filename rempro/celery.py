import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rempro.settings")

app = Celery("rempro")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "process-service-invoices-daily": {
        "task": "buildings.tasks.process_service_invoices",
        "schedule": crontab(hour=8, minute=0),
        "args": (),
    },
}
