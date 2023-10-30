from django_filters import rest_framework

from recipes.models import Recipe, Tag, User


class RecipeFilter(rest_framework.FilterSet):
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug', to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = rest_framework.BooleanFilter()
    is_in_shopping_cart = rest_framework.BooleanFilter()
    author = rest_framework.ModelChoiceFilter(
        queryset=User.objects.all(), to_field_name='id',
        field_name='author'
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']


class IngredientFilter(rest_framework.FilterSet):
    def filter_queryset(self, queryset):
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__startswith=name)
        return queryset
