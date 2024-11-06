from django.contrib import admin
from .models import New, Post, PostCategory, Author


admin.site.register(New)
admin.site.register(Author)
admin.site.register(Post)
admin.site.register(PostCategory)