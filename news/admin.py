from django.contrib import admin
from .models import New, Post, PostCategory, Author, Category, Comment
from modeltranslation.admin import TranslationAdmin  # импортируем модель админки


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
