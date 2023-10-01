import base64
import re

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite, Follow, Ingridient, Recipe, RecipeIngridient, Tag, User
)


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
        read_only_fields = ['is_subscribed']


class TagSerializer(serializers.ModelSerializer):
    color = ColorField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngridientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingridient
        fields = ['name', 'measurement_unit']


class RecipeIngridientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingridient.id')
    name = serializers.ReadOnlyField(source='ingridient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingridient.measurement_unit'
    )

    class Meta:
        model = RecipeIngridient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeIngridientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingridient.objects.all())

    class Meta:
        model = RecipeIngridient
        fields = ['id', 'amount']

    def to_representation(self, instance):
        """Метод для корректной записи amount в RecipeIngridient."""
        recipe_ingridients = RecipeIngridient.objects.filter(
            ingridient=instance
        )
        representation = []
        for recipe_ingridient in recipe_ingridients:
            for rep in representation:
                if rep['id'] == instance.id:
                    rep['amount'] = recipe_ingridient.amount
                    break
            else:
                representation.append(
                    {
                        'id': instance.id,
                        'amount': recipe_ingridient.amount
                    }
                )
        return representation


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingridients = RecipeIngridientReadSerializer(
        many=True, source='recipeingridient_set', read_only=True
    )
    image = Base64ImageField(required=False, allow_null=True)
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingridients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        ]
        read_only_fields = ['is_favorited', 'is_in_shopping_cart']


class RecipeWriteSerializer(serializers.ModelSerializer):
    author = UserSerializer(required=False)
    ingridients = RecipeIngridientWriteSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingridients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        ]
        read_only_fields = ['is_favorited', 'is_in_shopping_cart']

    def create(self, validated_data):
        ingridients_data = validated_data.pop('ingridients')
        tags_data = validated_data.pop('tags')
        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        for ingridient_data in ingridients_data:
            RecipeIngridient.objects.create(
                recipe=recipe, ingridient=ingridient_data['id'],
                amount=ingridient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingridients_data = validated_data.pop('ingridients')
        instance = super().update(instance, validated_data)
        instance.recipeingridient_set.all().delete()
        for ingridient_data in ingridients_data:
            RecipeIngridient.objects.create(
                recipe=instance, ingridient=ingridient_data['id'],
                amount=ingridient_data['amount']
            )
        return instance


class RecipeReadForFollowerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class UserWithRecipeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'username', 'email',
            'is_subscribed', 'recipes', 'recipes_count'
        ]

    def get_is_subscribed(self, obj):
        if obj.follower:
            return True
        return False

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        serializer = RecipeReadForFollowerSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        return recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    following = UserWithRecipeSerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Follow
        fields = ['following']
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(), fields=['follower', 'following']
            )
        ]

    def to_representation(self, instance):
        """Изменение формата вывода поля following."""
        representation = super().to_representation(instance)
        new_representation = representation.pop('following')
        return new_representation

    def validate_following(self, value):
        """Валидация подписки на самого себя."""
        user = self.context['request'].user
        if value == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        return value

    # def create(self, validated_data):
    #     user = self.context['request'].user
    #     following_id = validated_data.get('following')['id']
    #     following = User.objects.get(id=following_id)
    #     return Follow.objects.create(follower=user, following=following)


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = RecipeReadForFollowerSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ['recipe']
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['follower', 'recipe']
            )
        ]

    def to_representation(self, instance):
        """Изменение формата вывода поля recipe."""
        representation = super().to_representation(instance)
        new_representation = representation.pop('recipe')
        return new_representation
