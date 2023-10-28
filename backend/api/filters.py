from django_filters import rest_framework

from recipes.models import Recipe, Tag


class RecipeFilter(rest_framework.FilterSet):
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug', to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author']

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        user = self.request.user
        if self.request.GET.get('author'):
            queryset = queryset.filter(
                author__id=self.request.GET.get('author')
            )
        if self.request.GET.get('is_favorited') == '1':
            queryset = queryset.filter(recipes_favorite_related__follower=user)
        if self.request.GET.get('is_in_shopping_cart') == '1':
            queryset = queryset.filter(
                recipes_shoppingcart_related__follower=user
            )
        return queryset


class IngredientFilter(rest_framework.FilterSet):
    def filter_queryset(self, queryset):
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__startswith=name)
        return queryset
