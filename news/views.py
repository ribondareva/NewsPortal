import logging

import pytz  # Импортируем модуль для работы с часовыми поясами
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.cache import cache
from django.db.models import Exists
from django.db.models import OuterRef
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.timezone import activate
from django.utils.timezone import localtime
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from .filters import PostFilter
from .forms import CommentForm
from .forms import PostForm
from .models import Category
from .models import Post
from .models import Subscription
from .tasks import notify_about_new_post


class TimezoneMixin:
    """Миксин для работы с часовыми поясами."""

    def get_timezones_context(self):
        """Добавляет часовые пояса в контекст."""
        current_time = localtime(now())
        user_timezone = self.request.session.get("django_timezone", "UTC")
        return {
            "current_time": current_time,
            "timezones": pytz.common_timezones,
            "TIME_ZONE": user_timezone,
        }


class PostsList(ListView, TimezoneMixin):
    model = Post
    ordering = "-creationDate"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        if self.request.path.startswith("/news/"):
            queryset = self.filterset.qs.filter(categoryType="NW")
        elif self.request.path.startswith("/articles/"):
            queryset = self.filterset.qs.filter(categoryType="AR")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset
        # Добавляем часовые пояса в контекст
        context.update(self.get_timezones_context())
        return context

    def post(self, request, *args, **kwargs):
        """Обрабатываем выбор часового пояса."""
        timezone_name = request.POST.get("timezone", None)
        if timezone_name in pytz.common_timezones:
            request.session["django_timezone"] = timezone_name
        return redirect(self.request.path)

    def get_template_names(self):
        if self.request.path == "/post/search/":
            return "search.html"
        return "news.html"


class PostDetail(DetailView):
    model = Post
    template_name = "post.html"
    context_object_name = "post"
    queryset = Post.objects.all()

    def get_object(self, *args, **kwargs):  # переопределяем метод получения объекта
        obj = cache.get(f'product-{self.kwargs["pk"]}', None)
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'product-{self.kwargs["pk"]}', obj)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем комментарии, связанные с текущим постом
        context["comments"] = self.object.comment_set.all()
        # Часовой пояс из сессии
        user_timezone = self.request.session.get("django_timezone", "UTC")
        activate(user_timezone)

        context["timezones"] = pytz.common_timezones
        context["current_time"] = localtime(now())  # Локализованное время
        context["TIME_ZONE"] = user_timezone  # для шаблона
        return context


logger = logging.getLogger(__name__)  # Настраиваем логгер


class PostCreate(PermissionRequiredMixin, TimezoneMixin, CreateView):
    permission_required = ("news.add_post",)
    model = Post
    form_class = PostForm
    template_name = "post_edit.html"

    def form_valid(self, form):
        try:
            post = form.save(commit=False)
            if self.request.path == "/post/articles/create/":
                post.categoryType = "AR"
            if self.request.path.startswith("/post/news/"):
                post.categoryType = "NW"
            elif self.request.path.startswith("/post/articles/"):
                post.categoryType = "AR"
            if not post.author:
                raise ValueError("У поста должен быть автор")
            post.save()
            # Запускаем Celery задачу для уведомления подписчиков
            notify_about_new_post.delay(post_id=post.pk)
        except Exception as e:
            logger.error(f"Ошибка при сохранении поста или запуске задачи: {e}")
            raise
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_timezones_context())
        return context


class PostEdit(PermissionRequiredMixin, TimezoneMixin, UpdateView):
    permission_required = ("news.change_post",)
    model = Post
    form_class = PostForm
    template_name = "post_edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_timezones_context())
        return context


class PostDelete(PermissionRequiredMixin, TimezoneMixin, DeleteView):
    permission_required = ("news.delete_post",)
    model = Post
    template_name = "post_delete.html"
    success_url = reverse_lazy("post_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_timezones_context())
        return context


class CategoryListView(TimezoneMixin, ListView):
    model = Category
    template_name = "category_list.html"
    context_object_name = "category_news_list"

    def get_queryset(self):
        self.category = get_object_or_404(Category, id=self.kwargs["pk"])
        queryset = Post.objects.filter(category=self.category).order_by("-creationDate")
        # Аннотируем категории, чтобы передать состояние подписки
        return queryset.annotate(
            user_subscribed=Exists(
                Subscription.objects.filter(
                    user=self.request.user,  # Текущий пользователь
                    category=OuterRef("pk"),  # Сравнение по категории
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_not_subscriber"] = (
            not self.get_queryset().filter(user_subscribed=True).exists()
        )
        context["category"] = self.category
        context.update(self.get_timezones_context())
        return context


# Создание комментария
class CreateCommentView(PermissionRequiredMixin, View):
    permission_required = "news.can_add_comment"
    raise_exception = True  # Поднимает исключение, если прав недостаточно
    template_name = "create_comment.html"

    def get(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        form = CommentForm()
        return render(request, self.template_name, {"form": form, "post": post})

    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.commentUser = request.user
            comment.commentPost = post
            comment.save()
            return redirect("post_detail", pk=pk)
        return render(request, self.template_name, {"form": form, "post": post})


@login_required
@csrf_protect
def subscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.add(user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "subscribe":
            Subscription.objects.get_or_create(user=user, category=category)
        elif action == "unsubscribe":
            Subscription.objects.filter(user=user, category=category).delete()

    return redirect("subscriptions")  # Перенаправление на страницу подписок


def subscriptions(request):
    if request.method == "POST":
        category_id = request.POST.get("category_id")
        category = Category.objects.get(id=category_id)
        action = request.POST.get("action")

        if action == "subscribe":
            Subscription.objects.create(user=request.user, category=category)
        elif action == "unsubscribe":
            Subscription.objects.filter(
                user=request.user,
                category=category,
            ).delete()

    categories_with_subscriptions = Category.objects.annotate(
        user_subscribed=Exists(
            Subscription.objects.filter(
                user=request.user,
                category=OuterRef("pk"),
            )
        )
    ).order_by("name")
    return render(
        request,
        "subscriptions.html",
        {"categories": categories_with_subscriptions},
    )


class HomePage(TemplateView, TimezoneMixin):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_timezone = self.request.session.get("django_timezone", "UTC")
        activate(user_timezone)
        context["timezones"] = pytz.common_timezones
        context["current_time"] = localtime(now())
        context["user_timezone"] = user_timezone
        context["TIME_ZONE"] = user_timezone
        return context

    def post(self, request, *args, **kwargs):
        """Обрабатываем выбор часового пояса."""
        timezone_name = request.POST.get("timezone", None)
        if timezone_name in pytz.common_timezones:
            request.session["django_timezone"] = timezone_name
            activate(timezone_name)
        return redirect(self.request.path)
