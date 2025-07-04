import logging
from datetime import datetime
from datetime import timedelta

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Category
from .models import Post
from NewsPortal import settings


def send_notifications(preview, pk, title, subscribers):
    """
    Фоновая задача для отправки email-уведомлений о новом посте.
    """
    html_content = render_to_string(
        "post_created_email.html",
        {
            "text": preview,
            "link": f"{settings.SITE_URL}/post/{pk}/",
        },
    )
    msg = EmailMultiAlternatives(
        subject=title,
        body="",  # Пустое текстовое тело, так как основное содержимое в HTML
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=subscribers,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


@shared_task(bind=True)
def notify_about_new_post(self, post_id):
    """
    Задача для уведомления подписчиков о новом посте.
    Принимает ID поста, на основе которого отправляются уведомления.
    """

    try:
        post = Post.objects.get(pk=post_id)  # Получаем пост по ID
        categories = post.category.all()  # Получаем связанные категории
        subscribers = set()  # Используем множество, чтобы избежать дублирования

        for category in categories:
            subscribers.update(
                category.subscribers.all()
            )  # Добавляем подписчиков категории

        # Получаем email-адреса подписчиков
        subscriber_emails = [subscriber.email for subscriber in subscribers]
        if not subscriber_emails:
            logger.info(f"Нет подписчиков для поста ID {post_id}")
            return

        # Отправляем уведомления
        send_notifications(
            preview=post.preview(),
            pk=post.pk,
            title=post.title,
            subscribers=subscriber_emails,
        )
    except Post.DoesNotExist:
        logger.error(f"Пост с ID {post_id} не найден")
        return


logger = logging.getLogger(__name__)  # Настраиваем логгер


@shared_task(bind=True)
def send_weekly_digest(self):
    """
    Рассылка последних новостей за неделю.
    """
    last_week = datetime.now() - timedelta(days=7)
    categories = Category.objects.all()

    for category in categories:
        try:
            # Получаем подписчиков категории
            subscribers = category.subscribers.all()
            if not subscribers.exists():
                continue  # Пропускаем категории без подписчиков

            # Собираем последние новости по категории
            posts = Post.objects.filter(
                category=category,
                creationDate__gte=last_week,
            )
            if not posts.exists():
                continue  # Пропускаем категории без новых постов

            # Список email-адресов подписчиков
            recipient_list = [user.email for user in subscribers]

            # Рендерим HTML для письма
            html_content = render_to_string(
                "daily_post.html",
                {
                    "posts": posts,
                    "category": category,
                    "link": settings.SITE_URL,
                },
            )

            # Создаём и отправляем письмо
            subject = f"Еженедельная подборка новостей: {category.name}"
            msg = EmailMultiAlternatives(
                subject=subject,
                body="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        except Exception as e:
            # Логируем ошибку, чтобы не терять информацию
            logger.error(
                f"Ошибка при отправке писем для категории {category.name}: {e}",
                exc_info=True,
            )
