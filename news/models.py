from datetime import datetime

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

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
    categoryType = models.CharField(max_length=2, choices=CATEGORY_CHOICES, default=NEWS)
    creationDate = models.DateTimeField(auto_now_add=True)
    category = models.ManyToManyField(Category, through="PostCategory")
    title = models.CharField(max_length=64)
    text = models.TextField()
    rating = models.SmallIntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def preview(self):
        return self.text[0:119] + "..."

    def get_absolute_url(self):
        return reverse("post_detail", args=[str(self.id)])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # сначала вызываем метод родителя, чтобы объект сохранился
        cache.delete(f"product-{self.pk}")  # затем удаляем его из кэша, чтобы сбросить его

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

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def __str__(self):
        return f"Комментарий от {self.commentUser} к {self.commentPost}"

    class Meta:
        permissions = [
            ("can_add_comment", "Can add comment"),
            ("can_delete_comment", "Can delete comment"),
        ]


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
