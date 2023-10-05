from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from djoser.views import UserViewSet
from rest_framework import (
    filters, mixins, permissions, serializers, status, viewsets
)
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (
    Favorite, Follow, Ingridient, Recipe, RecipeIngridient, ShoppingCart, Tag,
    User
)
from .serializers import (
    DownloadShoppingCartSerializer,
    FavoriteSerializer, FollowSerializer, IngridientSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, ShoppingCartSerializer,
    TagSerializer
)


class CustomUserViewSet(UserViewSet):
    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        user = request.user
        following = user.follower.all()
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


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['author', 'tags']

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

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
        ingridients = RecipeIngridient.objects.filter(recipe__in=recipes)
        ingridients = ingridients.values(
            'ingridient__name', 'ingridient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        groceries_list = 'Список покупок:'
        for ingridient in ingridients:
            groceries_list += (
                f'\n'
                f'{ingridient["ingridient__name"]}'
                f' - {ingridient["amount"]}'
                f'{ingridient["ingridient__measurement_unit"]}'
            )
        response = HttpResponse(groceries_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename=groceries_list.txt'
        )
        return response


class IngridientViewSet(viewsets.ModelViewSet):
    queryset = Ingridient.objects.all()
    serializer_class = IngridientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
