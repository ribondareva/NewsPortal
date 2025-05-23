from django.urls import path

from .views import CategoryListView
from .views import CreateCommentView
from .views import dislike_comment
from .views import dislike_post
from .views import like_comment
from .views import like_post
from .views import PostCreate
from .views import PostDelete
from .views import PostDetail
from .views import PostEdit
from .views import PostsList
from .views import subscribe
from .views import subscriptions
from .views import undislike_comment
from .views import undislike_post
from .views import unlike_comment
from .views import unlike_post


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
    path("<int:pk>/comment/", CreateCommentView.as_view(), name="create_comment"),
    path("categories/<int:pk>", CategoryListView.as_view(), name="category_list"),
    path("categories/<int:pk>/subscribe", subscribe, name="subscribe"),
    path("subscriptions/", subscriptions, name="subscriptions"),
    path("<int:pk>/like/", like_post, name="like_post"),
    path("<int:pk>/unlike/", unlike_post, name="unlike_post"),
    path("<int:pk>/dislike/", dislike_post, name="dislike_post"),
    path("<int:pk>/undislike/", undislike_post, name="undislike_post"),
    path("comment/<int:pk>/like/", like_comment, name="like_comment"),
    path("comment/<int:pk>/unlike/", unlike_comment, name="unlike_comment"),
    path("comment/<int:pk>/dislike/", dislike_comment, name="dislike_comment"),
    path("comment/<int:pk>/undislike/", undislike_comment, name="undislike_comment"),
]
