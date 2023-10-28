from django.contrib import admin

from recipes.forms import RecipeForm, TagForm
from recipes.models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
    Tag, User
)


class UserAdmin(admin.ModelAdmin):
    list_filter = ['email', 'username']


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    autocomplete_fields = ['ingredient']
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = ('publication_date', 'get_favorite_count')
    list_filter = ['author', 'name', 'tags']
    inlines = (RecipeIngredientInLine, )
    form = RecipeForm

    def get_favorite_count(self, obj):
        """Вычисляет количество добавлений рецепта в избранное."""
        total = obj.recipes_favorite_related.all().count()
        return total

    get_favorite_count.short_description = (
        'Количество добавлений рецепта в избранное'
    )


class IngredientAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    list_filter = ['name']
    search_fields = ['name']


class TagAdmin(admin.ModelAdmin):
    form = TagForm


admin.site.register(User, UserAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(RecipeIngredient)
admin.site.register(Follow)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
