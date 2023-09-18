import base64
import re

from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import Ingridient, Recipe, Tag


class ColorField(serializers.CharField):
    """Валидация цвета для поля модели Tag."""
    def to_internal_value(self, data):
        if not re.match('^#(?:[0-9a-fA-F]{3}){1,2}$', data):
            raise serializers.ValidationError(
                'Такого цвета нет. Пожалуйста, используйте другой цвет.'
            )
        return super().to_internal_value(data)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    color = ColorField()

    class Meta:
        model = Tag
        fields = ['name', 'color', 'slug']


class IngridientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingridient
        fields = ['name', 'measurement_unit']


class RecipeIngridientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingridient
        fields = ['ingridient', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    ingridients = RecipeIngridientSerializer(required=True, many=True)
    image = Base64ImageField(required=False, allow_null=True)
    image_url = serializers.SerializerMethodField(
        'get_image_url',
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = [
            'author', 'tags', 'ingridients', 'is_favorited', 'name',
            'is_in_shopping_cart', 'image', 'text', 'cooking_time', 'image_url'
        ]
        read_only_fields = ['is_favorited', 'is_in_shopping_cart']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
