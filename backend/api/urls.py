from rest_framework import routers

from .views import (
    CustomUserViewSet, IngridientViewSet, RecipeViewSet, TagViewSet
)

router = routers.DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingridients', IngridientViewSet, basename='ingridients')
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = router.urls
