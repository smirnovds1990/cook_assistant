from django_filters import rest_framework

from recipes.models import Recipe, Tag


class RecipeTagFilter(rest_framework.FilterSet):
    '''Фильтрация рецепта по тегам.'''
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug', to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ['tags']
