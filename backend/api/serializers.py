import base64
import re

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
    Tag, User
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
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed'
        ]
        read_only_fields = ['is_subscribed']

    def get_is_subscribed(self, obj):
        if obj.follower:
            return False
        return True


class TagSerializer(serializers.ModelSerializer):
    color = ColorField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']

    def to_representation(self, instance):
        """Метод для корректной записи amount в RecipeIngredient."""
        recipe_ingredients = RecipeIngredient.objects.filter(
            ingredient=instance
        )
        representation = []
        for recipe_ingredient in recipe_ingredients:
            for rep in representation:
                if rep['id'] == instance.id:
                    rep['amount'] = recipe_ingredient.amount
                    break
            else:
                representation.append(
                    {
                        'id': instance.id,
                        'amount': recipe_ingredient.amount
                    }
                )
        return representation


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, source='recipeingredient_set', read_only=True
    )
    image = Base64ImageField(required=False, allow_null=True)
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        ]
        read_only_fields = ['is_favorited', 'is_in_shopping_cart', 'tags']

    def get_is_favorited(self, obj):
        if obj.recipes_favorite_related.filter(
            follower=self.context['request'].user
        ):
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        if obj.recipes_shoppingcart_related.filter(
            follower=self.context['request'].user
        ):
            return True
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    author = UserSerializer(required=False)
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        ]
        read_only_fields = ['is_favorited', 'is_in_shopping_cart']

    def get_is_favorited(self, obj):
        if obj.recipes_favorite_related.filter(
            follower=self.context['request'].user
        ):
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        if obj.recipes_shoppingcart_related.filter(
            follower=self.context['request'].user
        ):
            return True
        return False

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.recipeingredient_set.all().delete()
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=instance, ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
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
    following = UserWithRecipeSerializer()

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


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = RecipeReadForFollowerSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
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
