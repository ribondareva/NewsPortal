from django.contrib import admin
from modeltranslation.admin import TranslationAdmin  # импортируем модель админки

from .models import Author
from .models import Category
from .models import Comment
from .models import Like
from .models import New
from .models import Post
from .models import PostCategory


# Регистрируем модели для перевода в админке


class CategoryAdmin(TranslationAdmin):
    model = Category


class PostAdmin(TranslationAdmin):
    model = Post


admin.site.register(New)
admin.site.register(Comment)
admin.site.register(Author)
admin.site.register(Post)
admin.site.register(PostCategory)
admin.site.register(Category)
admin.site.register(Like)
