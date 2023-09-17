import re

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


class TagSerializer(serializers.ModelSerializer):
    color = ColorField()

    class Meta:
        model = Tag
        fields = ['name', 'color', 'slug']


class IngridientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingridient
        fields = ['name', 'measurement_unit']


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ['is_favorited', 'is_in_shopping_cart']
