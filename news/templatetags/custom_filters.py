import re

from django import template


register = template.Library()
censored_words = ["редиска", "картошка"]
pattern = r"\b(?:" + "|".join(censored_words) + r")\b"


@register.filter()
def censor(value):
    """
    Заменяет слова "редиска" и "Редиска" на "р******" и "Р******" соответственно.
    """
    if isinstance(value, str):

        def replace_with_original_case(match):
            return "р******" if match.group().islower() else "Р******"

        pattern = r"\b(Редиска|редиска)\b"
        return re.sub(pattern, replace_with_original_case, value)
    else:
        raise TypeError("Фильтр censor может применяться только к строкам")
