from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django_ckeditor_5.fields import CKEditor5Field

# from django.utils.translation import (
#     pgettext_lazy,
# )  # импортируем «ленивый» геттекст с подсказкой


class Author(models.Model):
    authorUser = models.OneToOneField(User, on_delete=models.CASCADE)
    ratingAuthor = models.SmallIntegerField(default=0)

    def update_rating(self):
        postRat = self.post_set.aggregate(postRating=Sum("rating"))
        pRat = postRat.get("postRating") or 0

        commentRat = self.authorUser.comment_set.aggregate(commentRating=Sum("rating"))
        cRat = commentRat.get("commentRating") or 0

        self.ratingAuthor = pRat * 3 + cRat
        self.save()

    def __str__(self):
        return self.authorUser.username


class Category(models.Model):
    name = models.CharField(max_length=32, unique=True, help_text=_("category name"))
    subscribers = models.ManyToManyField(User, related_name="categories")

    def __str__(self):
        return self.name


class Post(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    NEWS = "NW"
    ARTICLE = "AR"
    CATEGORY_CHOICES = (
        (NEWS, "News"),
        (ARTICLE, "Article"),
    )
    categoryType = models.CharField(
        max_length=2, choices=CATEGORY_CHOICES, default=NEWS
    )
    creationDate = models.DateTimeField(auto_now_add=True)
    category = models.ManyToManyField(Category, through="PostCategory")
    title = models.CharField(max_length=64)
    text = CKEditor5Field("Text", config_name="default")
    rating = models.SmallIntegerField(default=0)

    def preview(self):
        return self.text[0:119] + "..."

    def get_absolute_url(self):
        return reverse("post_detail", args=[str(self.id)])

    def save(self, *args, **kwargs):
        super().save(
            *args, **kwargs
        )  # сначала вызываем метод родителя, чтобы объект сохранился
        cache.delete(f"post-{self.pk}")  # затем удаляем его из кэша, чтобы сбросить его

    def add_like(self, user):
        if self.user_disliked(user):
            self.remove_dislike(user)
        if not self.user_liked(user):
            Like.objects.create(user=user, content_object=self)
            self.rating += 1
            self.save()
            self.author.update_rating()

    def remove_like(self, user):
        content_type = ContentType.objects.get_for_model(self)
        like = Like.objects.filter(
            user=user, content_type=content_type, object_id=self.id
        )
        if like.exists():
            like.delete()
            self.rating = max(0, self.rating - 1)
            self.save()
            self.author.update_rating()

    def user_liked(self, user):
        content_type = ContentType.objects.get_for_model(self)
        return Like.objects.filter(
            user=user, content_type=content_type, object_id=self.id
        ).exists()

    def get_likes_count(self):
        content_type = ContentType.objects.get_for_model(self)
        return Like.objects.filter(content_type=content_type, object_id=self.id).count()

    def add_dislike(self, user):
        if self.user_liked(user):
            self.remove_like(user)
        if not self.user_disliked(user):
            Dislike.objects.create(user=user, content_object=self)
            self.rating = max(0, self.rating - 1)
            self.save()
            if hasattr(self, "author"):
                self.author.update_rating()

    def remove_dislike(self, user):
        content_type = ContentType.objects.get_for_model(self)
        dislike = Dislike.objects.filter(
            user=user, content_type=content_type, object_id=self.id
        )
        if dislike.exists():
            dislike.delete()
            self.rating += 1
            self.save()
            if hasattr(self, "author"):
                self.author.update_rating()

    def user_disliked(self, user):
        content_type = ContentType.objects.get_for_model(self)
        return Dislike.objects.filter(
            user=user, content_type=content_type, object_id=self.id
        ).exists()

    def get_dislikes_count(self):
        content_type = ContentType.objects.get_for_model(self)
        return Dislike.objects.filter(
            content_type=content_type, object_id=self.id
        ).count()

    class Meta:
        permissions = [
            ("can_add_comment", "Can add comment"),
        ]


class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class Comment(models.Model):
    commentPost = models.ForeignKey(Post, on_delete=models.CASCADE)
    commentUser = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    creationDate = models.DateTimeField(auto_now_add=True)
    rating = models.SmallIntegerField(default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"Комментарий от {self.commentUser} к {self.commentPost}"

    def add_like(self, user):
        if self.user_disliked(user):
            self.remove_dislike(user)
        if not self.user_liked(user):
            Like.objects.create(user=user, content_object=self)
            self.rating += 1
            self.save()
            if hasattr(self.commentUser, "author"):
                self.commentUser.author.update_rating()

    def remove_like(self, user):
        ct = ContentType.objects.get_for_model(self)
        qs = Like.objects.filter(user=user, content_type=ct, object_id=self.id)
        if qs.exists():
            qs.delete()
            self.rating = max(0, self.rating - 1)
            self.save()
            if hasattr(self.commentUser, "author"):
                self.commentUser.author.update_rating()

    def user_liked(self, user):
        ct = ContentType.objects.get_for_model(self)
        return Like.objects.filter(
            user=user, content_type=ct, object_id=self.id
        ).exists()

    def get_likes_count(self):
        ct = ContentType.objects.get_for_model(self)
        return Like.objects.filter(content_type=ct, object_id=self.id).count()

        # ── дизлайки ───────────────────────────────

    def add_dislike(self, user):
        if self.user_liked(user):
            self.remove_like(user)
        if not self.user_disliked(user):
            Dislike.objects.create(user=user, content_object=self)
            self.rating = max(0, self.rating - 1)
            self.save()
            if hasattr(self.commentUser, "author"):
                self.commentUser.author.update_rating()

    def remove_dislike(self, user):
        ct = ContentType.objects.get_for_model(self)
        qs = Dislike.objects.filter(user=user, content_type=ct, object_id=self.id)
        if qs.exists():
            qs.delete()
            self.rating += 1
            self.save()
            if hasattr(self.commentUser, "author"):
                self.commentUser.author.update_rating()

    def user_disliked(self, user):
        ct = ContentType.objects.get_for_model(self)
        return Dislike.objects.filter(
            user=user, content_type=ct, object_id=self.id
        ).exists()

    def get_dislikes_count(self):
        ct = ContentType.objects.get_for_model(self)
        return Dislike.objects.filter(content_type=ct, object_id=self.id).count()

    class Meta:
        permissions = [
            ("can_add_comment", "Can add comment"),
            ("can_delete_comment", "Can delete comment"),
        ]


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "content_type", "object_id")
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"{self.user} → {self.content_object}"


class Dislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "content_type", "object_id")
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"{self.user} 👎 {self.content_object}"


class New(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    pub_date = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"{self.title} {self.pub_date.strftime('%d.%m.%Y')} {self.text}"

    def get_absolute_url(self):
        return reverse("new_detail", args=[str(self.id)])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pub_date"] = datetime.utcnow()
        return context


class Subscription(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    category = models.ForeignKey(
        to="Category",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
