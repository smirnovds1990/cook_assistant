import base64
import re

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Ingridient, Recipe, RecipeIngridient, Tag, User


class ColorField(serializers.CharField):
    """Валидация цвета для поля модели Tag."""
    def to_internal_value(self, data):
        if not re.match('^#(?:[0-9a-fA-F]{3}){1,2}$', data):
            raise serializers.ValidationError(
                'Такого цвета нет. Пожалуйста, используйте другой цвет.'
            )
        return super().to_internal_value(data)


class Base64ImageField(serializers.ImageField):
    """Декодирование и сохраниние картинок."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'username', 'email',
            'is_subscribed'
        ]
        read_only_fields = ['email', 'is_subscribed', 'username']


class TagSerializer(serializers.ModelSerializer):
    color = ColorField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngridientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingridient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngridientSerializer(serializers.ModelSerializer):
    ingridient = IngridientSerializer(read_only=True)
    # ingridient = serializers.PrimaryKeyRelatedField(
    #     queryset=Ingridient.objects.all()
    # )

    class Meta:
        model = RecipeIngridient
        fields = ['ingridient', 'amount']


class RecipeIngridientWriteSerializer(serializers.ModelSerializer):
    ingridient = serializers.PrimaryKeyRelatedField(
        queryset=Ingridient.objects.all()
    )

    class Meta:
        model = RecipeIngridient
        fields = ['ingridient', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True, required=False)
    ingridients = RecipeIngridientSerializer(
        many=True, source='recipeingridient_set'
    )
    # ingridients = RecipeIngridientWriteSerializer()
    image = Base64ImageField(required=False, allow_null=True)
    # image_url = serializers.SerializerMethodField(
    #     'get_image_url',
    #     read_only=True,
    # )
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingridients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        ]
        read_only_fields = ['is_favorited', 'is_in_shopping_cart']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def create(self, validated_data):
        ingridients_data = validated_data.pop('ingridients', [])
        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        for ingridient_data in ingridients_data:
            ingridient = get_object_or_404(
                Ingridient, id=ingridient_data['id']
            )
            RecipeIngridient.objects.create(
                recipe=recipe,
                ingridient=ingridient,
                amount=ingridient_data['amount']
            )
        return recipe
    # def create(self, validated_data):
    #     ingridients = validated_data.pop('ingridients', [])
    #     author = self.context['request'].user
    #     recipe = Recipe.objects.create(author=author, **validated_data)
    #     for ingridient in ingridients:
    #         RecipeIngridient.objects.create(recipe=recipe, **ingridient)
    #     return recipe

    def update(self, instance, validated_data):
        ingridients = validated_data.pop('ingridients', [])
        instance = super().update(instance, validated_data)
        instance.recipeingridient_set.all().delete()
        for ingridient in ingridients:
            RecipeIngridient.objects.create(recipe=instance, **ingridient)
        return instance
