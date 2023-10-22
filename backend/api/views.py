from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import (
    mixins, permissions, serializers, status, viewsets
)
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import RecipeTagFilter
from recipes.models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
    User
)
from .serializers import (
    FavoriteSerializer, FollowSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, ShoppingCartSerializer,
    TagSerializer, UserSerializer
)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        user = request.user
        following = user.follower.all()
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = FollowSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(following, many=True)
        return Response(serializer.data)

    @action(methods=['post', 'delete'], detail=True)
    def subscribe(self, request, id=None):
        user = request.user
        following = User.objects.get(id=id)
        if self.request.method == 'POST':
            if user == following:
                raise serializers.ValidationError(
                    'Нельзя подписаться на самого себя!'
                )
            follow = Follow.objects.create(follower=user, following=following)
            serializer = FollowSerializer(follow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        follow = Follow.objects.get(follower=user, following=following)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    paginator = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeTagFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
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

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk=None):
        user = request.user
        recipe = Recipe.objects.get(pk=pk)
        if self.request.method == 'POST':
            favorite = Favorite.objects.create(
                follower=user, recipe=recipe)
            serializer = FavoriteSerializer(favorite)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        favorite = Favorite.objects.get(follower=user, recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = Recipe.objects.get(pk=pk)
        if self.request.method == 'POST':
            shopping_cart = ShoppingCart.objects.create(
                follower=user, recipe=recipe
            )
            serializer = ShoppingCartSerializer(shopping_cart)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        shopping_cart = ShoppingCart.objects.get(follower=user, recipe=recipe)
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        user = request.user
        shopping_carts = user.follower_recipes_shoppingcart_related.all()
        recipes = [cart.recipe for cart in shopping_carts]
        ingredients = RecipeIngredient.objects.filter(recipe__in=recipes)
        ingredients = ingredients.values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        groceries_list = 'Список покупок:'
        for ingredient in ingredients:
            groceries_list += (
                f'\n'
                f'{ingredient["ingredient__name"]}'
                f' - {ingredient["amount"]}'
                f'{ingredient["ingredient__measurement_unit"]}'
            )
        response = HttpResponse(groceries_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename=groceries_list.txt'
        )
        return response


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    paginator = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name__startswith=name)
        return queryset
