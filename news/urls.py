from django.urls import path

from .views import (
    PostsList,
    PostDetail,
    PostCreate,
    PostEdit,
    PostDelete,
    subscriptions,
    CategoryListView,
    subscribe,
)


urlpatterns = [
    path("", PostsList.as_view(), name="post_list"),
    path("<int:pk>/", PostDetail.as_view(), name="post_detail"),
    path("news/", PostsList.as_view(), name="news_list"),  # Новости
    path("articles/", PostsList.as_view(), name="articles_list"),  # Статьи
    path("articles/create/", PostCreate.as_view(), name="create_articles"),
    path("news/create/", PostCreate.as_view(), name="create_post"),
    path("search/", PostsList.as_view(), name="post_filter"),
    path("<int:pk>/edit/", PostEdit.as_view(), name="post_update"),
    path("<int:pk>/delete/", PostDelete.as_view(), name="post_delete"),
    path("categories/<int:pk>", CategoryListView.as_view(), name="category_list"),
    path("categories/<int:pk>/subscribe", subscribe, name="subscribe"),
    path("subscriptions/", subscriptions, name="subscriptions"),
]
