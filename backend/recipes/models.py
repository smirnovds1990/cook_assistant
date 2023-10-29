from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from .constants import (
    MAX_COLOR_FIELD_LENGTH, MAX_EMAIL_LENGTH, MAX_FIELD_LENGTH,
    MAX_NAMES_LENGTH
)
from .validators import (
    validate_ingredient_amount, validate_cooking_time, validate_hex_color
)


class User(AbstractUser):
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH, verbose_name='электронная почта',
        unique=True
    )
    username = models.CharField(
        max_length=MAX_NAMES_LENGTH, verbose_name='имя пользователя',
        unique=True
    )
    first_name = models.CharField(
        max_length=MAX_NAMES_LENGTH, verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_NAMES_LENGTH, verbose_name='Фамилия'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.username})'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH, verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_FIELD_LENGTH, verbose_name='Единицы измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH, verbose_name='Тег'
    )
    color = models.CharField(
        max_length=MAX_COLOR_FIELD_LENGTH, verbose_name='Цвет', null=True,
        validators=[validate_hex_color]
    )
    slug = models.CharField(
        max_length=MAX_FIELD_LENGTH, null=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор рецепта',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги', related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', related_name='recipes',
        verbose_name='Список ингредиентов'
    )
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH, verbose_name='Название'
    )
    image = models.ImageField(
        verbose_name='Фотография', upload_to='recipes/images/', null=True,
        default=None, blank=True
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[validate_cooking_time]
    )
    publication_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-publication_date']

    def __str__(self):
        return f'{self.name} ({self.author})'


class RecipeIngredient(models.Model):
    """Промежуточная модель для добавления количества ингредиента."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredient_amount'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество', validators=[validate_ingredient_amount]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.ingredient.name} ({self.recipe.name})'


class Follow(models.Model):
    """Модель для подписок на пользователей."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            )
        ]

    def save(self, *args, **kwargs):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя!')
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f'User: {self.user.get_full_name()} '
            f'Author: {self.author.get_full_name()}'
        )


class RecipeFollow(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_related'
    )
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower_%(app_label)s_%(class)s_related'
    )

    class Meta:
        abstract = True


class Favorite(RecipeFollow):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.recipe} (Подписчик: {self.follower})'


class ShoppingCart(RecipeFollow):
    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.recipe} (Подписчик: {self.follower})'
