from django.urls import path
from user_profile.views import profile, be_author


urlpatterns = [
    path("", profile, name="profile"),
    path("be_author/", be_author, name="be_author"),
]
