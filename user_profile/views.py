from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import render, get_object_or_404, redirect

from news.models import Author


@login_required
def profile(request):
    is_not_author = not request.user.groups.filter(name="authors").exists()
    return render(request, "profile.html", {"is_not_author": is_not_author})


@login_required
def be_author(request):
    user = request.user
    group = get_object_or_404(Group, name="authors")
    if not user.groups.filter(name=group.name).exists():
        user.groups.add(group)
    if not Author.objects.filter(authorUser=user).exists():
        Author.objects.create(authorUser=user)
    return redirect("profile")
