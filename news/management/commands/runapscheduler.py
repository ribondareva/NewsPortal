# from datetime import datetime, timedelta
# import pytz
# import logging
#
# from apscheduler.schedulers.blocking import BlockingScheduler
# from apscheduler.triggers.cron import CronTrigger
# from django.conf import settings
# from django.core.mail import EmailMultiAlternatives
# from django.core.management.base import BaseCommand
# from django.template.loader import render_to_string
# from django_apscheduler import util
# from django_apscheduler.jobstores import DjangoJobStore
# from django_apscheduler.models import DjangoJobExecution
#
# from news.models import Post, Category
#
# logger = logging.getLogger(__name__)
#
#
# def my_job():
#     # Явное указание часового пояса сервера (например, UTC)
#     tz = pytz.timezone('UTC')
#     today = datetime.now(tz)  # Текущее время с учетом часового пояса
#     last_week = today - timedelta(days=7)
#     posts = Post.objects.filter(creationDate__gte=last_week)
#     categories = set(posts.values_list('category__name', flat=True))
#     subscribers = set(Category.objects.filter(name__in=categories).
#     values_list('subscribers__email', flat=True))
#     html_content = render_to_string(
#         'daily_post.html',
# {
#             'link':settings.SITE_URL,
#             'posts':posts,
#          }
#     )
#     msg = EmailMultiAlternatives(
#         subject='Статьи за неделю',
#         body='',
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         to=subscribers,
#     )
#     msg.attach_alternative(html_content, 'text/html')
#     msg.send()
#
# #функция, которая будет удалять неактуальные задачи
# @util.close_old_connections
# def delete_old_job_executions(max_age=604_800):
#     DjangoJobExecution.objects.delete_old_job_executions(max_age)
#
#
# class Command(BaseCommand):
#     help = "Runs APScheduler."
#
#     def handle(self, *args, **options):
#         scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
#         scheduler.add_jobstore(DjangoJobStore(), "default")
#         # добавляем работу нашему задачнику
#         scheduler.add_job(
#             my_job,
#             trigger=CronTrigger(second="*/10"),  # то же что и интервал
#             id="my_job",  # уникальный id
#             max_instances=1,
#             replace_existing=True,
#         )
#         logger.info("Added job 'my_job'.")
#         # каждую неделю будут удаляться старые задачи,
#         # которые либо не удалось выполнить, либо уже выполнять не надо
#         scheduler.add_job(
#             delete_old_job_executions,
#             trigger=CronTrigger(
#                 day_of_week="fri", hour="18", minute="00"
#             ),
#             id="delete_old_job_executions",
#             max_instances=1,
#             replace_existing=True,
#         )
#         logger.info("Added weekly job: 'delete_old_job_executions'.")
#
#         try:
#             logger.info("Starting scheduler...")
#             scheduler.start()
#         except KeyboardInterrupt:
#             logger.info("Stopping scheduler...")
#             scheduler.shutdown()
#             logger.info("Scheduler shut down successfully!")
