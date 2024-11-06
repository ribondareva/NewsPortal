from django.urls import path
from .views import (
   PostsList, PostDetail, NewCreate, FilterList,
)


urlpatterns = [
   path('', PostsList.as_view(), name='post_list'),
   path('<int:pk>/', PostDetail.as_view(), name='new_detail'),
   path('create/', NewCreate.as_view(), name='create_post'),
   path('search/', FilterList.as_view(), name='post_filter'),

]