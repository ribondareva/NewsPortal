import pytest
from django.contrib.auth.models import User

from news.models import Author
from news.models import Comment
from news.models import Post


@pytest.mark.django_db
def test_author_rating_update():
    user = User.objects.create_user(username="testuser", password="12345")
    author = Author.objects.create(authorUser=user)
    post = Post.objects.create(
        author=author,
        title="Test Post",
        text="text",
        rating=5,
    )
    Comment.objects.create(
        commentPost=post,
        commentUser=user,
        text="Comment text",
        rating=2,
    )
    author.update_rating()
    assert author.ratingAuthor == 17
