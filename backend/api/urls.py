from rest_framework import routers

from .views import (
    CustomUserViewSet, IngredientViewSet, RecipeViewSet, TagViewSet
)

router = routers.DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'users', CustomUserViewSet, basename='users')

urlpatterns = router.urls
