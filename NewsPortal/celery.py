import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "NewsPortal.settings")

app = Celery("NewsPortal")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


app.conf.beat_schedule = {
    "send_weekly_digest_every_monday_8am": {
        "task": "news.tasks.send_weekly_digest",
        "schedule": crontab(hour=8, minute=0, day_of_week="monday"),
        "args": (),
    },
}
