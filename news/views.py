from django.contrib.auth.mixins import PermissionRequiredMixin


from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
)


from .forms import PostForm
from .filters import PostFilter
from .models import Post


class PostsList(ListView):
    model = Post
    ordering = '-creationDate'
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

    def get_template_names(self):
        if self.request.path == '/post/search/':
            return 'search.html'
        return 'news.html'



class PostDetail(DetailView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'


class PostCreate(PermissionRequiredMixin, CreateView):
    permission_required = ('news.add_post',)
    model = Post
    form_class = PostForm
    template_name = 'post_edit.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        if self.request.path == '/post/articles/create/':
            post.categoryType = 'AR'
        # post.author = self.request.user.author раскомментировать когда реализую авторизацию
        post.save()
        return redirect('post_detail', pk=post.pk)  # Перенаправляем на страницу с деталями новости

class PostEdit(PermissionRequiredMixin, UpdateView):
    permission_required = ('news.change_post',)
    raise_exception = True
    form_class = PostForm
    model = Post
    template_name = 'post_edit.html'

class PostDelete(PermissionRequiredMixin, DeleteView):
    permission_required = ('news.delete_post',)
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('post_list')


