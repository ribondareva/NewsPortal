import logging

import pytz  # Импортируем модуль для работы с часовыми поясами
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.cache import cache
from django.db.models import BooleanField
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Value
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
from .models import Comment
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
        if self.request.path.startswith("/news/"):
            queryset = self.filterset.qs.filter(categoryType="NW")
        elif self.request.path.startswith("/articles/"):
            queryset = self.filterset.qs.filter(categoryType="AR")
        self.filterset = PostFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

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

    def get_object(self, *args, **kwargs):  # кешируем пост
        obj = cache.get(f'post-{self.kwargs["pk"]}', None)
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'post-{self.kwargs["pk"]}', obj)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        post = self.object
        comments = post.comment_set.select_related("commentUser")

        # отметка, лайкнул ли текущий пользователь пост
        context["user_liked_post"] = (
            post.user_liked(user) if user.is_authenticated else False
        )
        context["user_disliked_post"] = (
            post.user_disliked(user) if user.is_authenticated else False
        )

        # для каждого комментария добавляем атрибут `user_liked_current`
        if user.is_authenticated:
            for c in comments:
                c.user_liked_current = c.user_liked(user)
                c.user_disliked_current = c.user_disliked(user)
        else:
            for c in comments:
                c.user_liked_current = False
                c.user_disliked_current = False

        context["comments"] = comments

        # данные часовых поясов
        user_tz = self.request.session.get("django_timezone", "UTC")
        activate(user_tz)
        context.update(
            {
                "timezones": pytz.common_timezones,
                "current_time": localtime(now()),
                "TIME_ZONE": user_tz,
            }
        )
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
        if self.request.user.is_authenticated:
            subscribed_expr = Exists(
                Subscription.objects.filter(
                    user_id=self.request.user.id,
                    category=OuterRef("pk"),
                )
            )
        else:
            # для анонимов всегда False
            subscribed_expr = Value(False, output_field=BooleanField())

        return queryset.annotate(user_subscribed=subscribed_expr)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            ctx["is_not_subscriber"] = not Subscription.objects.filter(
                user=self.request.user,
                category=self.category,
            ).exists()
        else:
            ctx["is_not_subscriber"] = True

        ctx["category"] = self.category
        ctx.update(self.get_timezones_context())
        return ctx


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
    # Сохраняем временную зону в сессию, если была отправлена
    timezone_name = request.POST.get("timezone")
    if timezone_name in pytz.common_timezones:
        request.session["django_timezone"] = timezone_name
        activate(timezone_name)
    else:
        timezone_name = request.session.get("django_timezone", "UTC")
        activate(timezone_name)

    if request.method == "POST" and "category_id" in request.POST:
        category_id = request.POST.get("category_id")
        category = Category.objects.get(id=category_id)
        action = request.POST.get("action")

        if action == "subscribe":
            Subscription.objects.get_or_create(user=request.user, category=category)
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
        {
            "categories": categories_with_subscriptions,
            "TIME_ZONE": timezone_name,
            "current_time": localtime(now()),
            "timezones": pytz.common_timezones,
        },
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


@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, id=pk)
    post.add_like(request.user)
    return redirect(post.get_absolute_url())


@login_required
def unlike_post(request, pk):
    post = get_object_or_404(Post, id=pk)
    post.remove_like(request.user)
    return redirect(post.get_absolute_url())


@login_required
def like_comment(request, pk):
    comment = get_object_or_404(Comment, id=pk)
    comment.add_like(request.user)
    return redirect(comment.commentPost.get_absolute_url())


@login_required
def unlike_comment(request, pk):
    comment = get_object_or_404(Comment, id=pk)
    comment.remove_like(request.user)
    return redirect(comment.commentPost.get_absolute_url())


@login_required
def dislike_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if post.user_disliked(request.user):
        post.remove_dislike(request.user)
    else:
        post.remove_like(request.user)  # чтобы нельзя было и лайк и дизлайк
        post.add_dislike(request.user)

    return redirect("post_detail", pk=pk)


@login_required
def undislike_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.remove_dislike(request.user)
    return redirect("post_detail", pk=pk)


@login_required
def dislike_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.user_disliked(request.user):
        comment.remove_dislike(request.user)
    else:
        comment.remove_like(request.user)
        comment.add_dislike(request.user)
    return redirect(comment.commentPost.get_absolute_url())


@login_required
def undislike_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.remove_dislike(request.user)
    return redirect(comment.commentPost.get_absolute_url())
