import re

from django.core.exceptions import ValidationError

from .constants import REGEX_FOR_HEX_COLOR


def validate_hex_color(value):
    if not re.match(REGEX_FOR_HEX_COLOR, value):
        raise ValidationError(
            ('%(value)s не является HEX цветом.'),
            params={'value': value},
        )


def validate_cooking_time(value):
    if value < 1:
        raise ValidationError(
            message='Время приготовления не может быть меньше 1 минуты.'
        )


def validate_ingredient_amount(value):
    if value == 0:
        raise ValidationError(
            message='Количество ингридиента не может быть 0.'
        )
