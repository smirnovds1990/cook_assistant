import base64
import re

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
    Tag, User
)
from recipes.constants import MIN_AMOUNT, MIN_COOKING_TIME, REGEX_FOR_HEX_COLOR


class ColorField(serializers.CharField):
    """Валидация цвета для поля модели Tag."""
    def to_internal_value(self, data):
        if not re.match(REGEX_FOR_HEX_COLOR, data):
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
        return (
            self.context['request'].user.is_authenticated
            and self.context['request'].user != obj
            and self.context['request'].user.follower.filter(
                author__id=obj.id
            ).exists()
        )


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


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, source='recipeingredient_set', read_only=True
    )
    image = Base64ImageField(required=False, allow_null=True)
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        ]
        read_only_fields = ['is_favorited', 'is_in_shopping_cart', 'tags']


class RecipeWriteSerializer(serializers.ModelSerializer):
    author = UserSerializer(required=False)
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'name', 'image', 'text',
            'cooking_time'
        ]

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Должен быть хотя бы один тег.')
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться!')
        for tag in value:
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(f'Тега {tag} не существует!')
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нельзя создать рецепт без ингредиентов!'
            )
        ingredient_ids = [ingredient['id'].id for ingredient in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться!'
            )
        for ingredient in value:
            if not Ingredient.objects.filter(id=ingredient['id'].id).exists():
                raise serializers.ValidationError(
                    f'Ингредиента {ingredient} не существует!'
                )
            if not ingredient['amount'] or ingredient['amount'] < MIN_AMOUNT:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть не меньше 1 ед. изм.'
                )
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'У рецепта должно быть изображение.'
            )
        if not value.name.endswith('.jpg') and not value.name.endswith('.png'):
            raise serializers.ValidationError(
                'Неверный формат файла. '
                'Загрузите файл в формате .jpg или .png.'
            )
        return value

    def validate_text(self, value):
        if not value:
            raise serializers.ValidationError('Должно быть описание рецепта!')
        return value

    def validate_cooking_time(self, value):
        if not value:
            raise serializers.ValidationError(
                'Вы забыли указать время приготовления.'
            )
        if value < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше одной минуты.'
            )
        return value

    @staticmethod
    def create_recipeingredient_objects(ingredients_data, recipe):
        """
        Создание объектов RecipeIngredient при создании и обновлении рецепта.
        """
        ingredients = []
        for ingredient_data in ingredients_data:
            ingredients.append(
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self.create_recipeingredient_objects(
            ingredients_data=ingredients_data, recipe=recipe
        )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)
        instance = super().update(instance, validated_data)
        instance.recipeingredient_set.all().delete()
        self.create_recipeingredient_objects(
            ingredients_data=ingredients_data, recipe=instance
        )
        return instance

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(instance, context=self.context)
        return serializer.data


class ShortRecipeReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class UserWithRecipeSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'username', 'email',
            'is_subscribed', 'recipes', 'recipes_count'
        ]

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get('recipes_limit', 3)
        recipes = obj.recipes.all()[:int(limit)]
        serializer = ShortRecipeReadSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ['user', 'author']
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(), fields=['user', 'author']
            )
        ]

    def to_representation(self, instance):
        """Изменение формата вывода поля author."""
        return UserWithRecipeSerializer(
            instance.author, context=self.context
        ).data

    def validate_author(self, value):
        user = self.context['request'].user
        if value == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        return value


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ['recipe', 'follower']
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['follower', 'recipe']
            )
        ]

    def to_representation(self, instance):
        """Изменение формата вывода поля recipe."""
        representation = ShortRecipeReadSerializer(instance.recipe).data
        return representation


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ['recipe', 'follower']
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['follower', 'recipe']
            )
        ]

    def to_representation(self, instance):
        """Изменение формата вывода поля recipe."""
        representation = ShortRecipeReadSerializer(instance.recipe).data
        return representation
