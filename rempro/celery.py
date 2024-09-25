import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rempro.settings")

app = Celery("rempro")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "add-every-30-seconds": {
        "task": "buildings.tasks.add",
        "schedule": 30.0,  # Her 30 saniyede bir çalışır
        "args": (16, 16),  # Görev parametreleri
    },
}
