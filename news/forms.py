from django import forms
from django.core.exceptions import ValidationError
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Category
from .models import Comment
from .models import Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ["author", "title", "category", "text"]
        widgets = {
            "text": CKEditor5Widget(config_name="default"),
        }

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get("text")
        title = cleaned_data.get("title")

        if title == text:
            raise ValidationError("Описание не должно быть идентично названию.")

        return cleaned_data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]


class SearchForm(forms.ModelForm):
    title = forms.CharField(required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    creationDate = forms.DateField(required=False)
