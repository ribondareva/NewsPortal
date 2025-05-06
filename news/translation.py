from modeltranslation.translator import register
from modeltranslation.translator import TranslationOptions

from .models import Category
from .models import Post


# регистрируем наши модели для перевода


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)  # указываем, какие именно поля надо переводить в виде кортежа


@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "text",
    )
