from django.views.generic import ListView, DetailView
from .models import New


class NewsList(ListView):
    model = New
    ordering = '-pub_date'
    template_name = 'news.html'
    context_object_name = 'news'

class NewDetail(DetailView):
    model = New
    template_name = 'new.html'
    context_object_name = 'new'