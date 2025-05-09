from django.forms import DateTimeInput
from django_filters import DateTimeFilter
from django_filters import FilterSet

from .models import Post


class PostFilter(FilterSet):
    creationDate = DateTimeFilter(
        field_name="creationDate",
        lookup_expr="gt",
        widget=DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
    )

    class Meta:
        model = Post
        fields = {
            "categoryType": ["exact"],
            "title": ["icontains"],
        }
