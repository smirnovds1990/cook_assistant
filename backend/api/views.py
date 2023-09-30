from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import Follow, Ingridient, Recipe, Tag, User
from .serializers import (
    FollowSerializer, IngridientSerializer, RecipeReadSerializer,
    RecipeWriteSerializer, TagSerializer, UserSerializer
)


class CustomUserViewSet(UserViewSet):
    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        user = request.user
        following = user.follower.all()
        serializer = FollowSerializer(following, many=True)
        return Response(serializer.data)


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

    # def get_queryset(self):
    #     return Recipe.objects.filter(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeWriteSerializer


class IngridientViewSet(viewsets.ModelViewSet):
    queryset = Ingridient.objects.all()
    serializer_class = IngridientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
