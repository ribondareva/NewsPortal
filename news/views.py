
from django.shortcuts import redirect
from django.views.generic import (
    ListView, DetailView, CreateView
)

from django import forms
from .forms import PostForm
from .filters import PostFilter
from .models import Post

from datetime import datetime

class PostsList(ListView):
    model = Post
    ordering = '-creationDate'
    template_name = 'news.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context


class FilterList(ListView):
    model = Post
    ordering = '-creationDate'
    template_name = 'search.html'
    context_object_name = 'posts'

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context



class PostDetail(DetailView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'


class NewCreate(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'new_edit.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.categoryType = 'NW'  # Устанавливаем тип "новость"
        # instance.author = self.request.user
        instance.save()
        return redirect('post.html', pk=instance.pk)  # Перенаправляем на страницу с деталями новости




class ArticleCreate(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'article_edit.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.categoryType = 'AR'  # Устанавливаем тип "статья"
        instance.save()
        return redirect('post', pk=instance.pk)  # Перенаправляем на страницу с деталями новости