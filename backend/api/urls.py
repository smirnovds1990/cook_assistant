from rest_framework import routers

from .views import IngridientViewSet, RecipeViewSet, TagViewSet

router = routers.DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'ingridients', IngridientViewSet)

urlpatterns = router.urls
