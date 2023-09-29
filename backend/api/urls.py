from rest_framework import routers

from .views import IngridientViewSet, RecipeViewSet, TagViewSet

router = routers.DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingridients', IngridientViewSet, basename='ingridients')

urlpatterns = router.urls
