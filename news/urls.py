from django.urls import path
from . import views
from .views import (
   PostsList, PostDetail, PostCreate, PostEdit, PostDelete
)


urlpatterns = [
   path('', PostsList.as_view(), name='post_list'),
   path('<int:pk>/', PostDetail.as_view(), name='post_detail'),
   path('articles/create/', PostCreate.as_view(), name='create_articles'),
   path('news/create/', PostCreate.as_view(), name='create_post'),
   path('search/', PostsList.as_view(), name='post_filter'),
   path('<int:pk>/edit/', PostEdit.as_view(), name='post_update'),
   path('<int:pk>/delete/', PostDelete.as_view(), name='post_delete'),

]