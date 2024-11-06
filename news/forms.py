from django import forms
from django.core.exceptions import ValidationError
from .models import Post, Category


class PostForm(forms.ModelForm):
    text = forms.CharField(min_length=20)
    author = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Post
        fields = ['title', 'text']


    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get("text")
        title = cleaned_data.get("title")

        if title == text:
            raise ValidationError(
                "Описание не должно быть идентично названию."
            )

        return cleaned_data

class SearchForm(forms.ModelForm):
    title = forms.CharField(required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    creationDate = forms.DateField(required=False)


