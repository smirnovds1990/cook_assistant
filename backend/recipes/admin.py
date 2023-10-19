from django.contrib import admin

from .models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
    Tag, User
)


class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('is_subscribed', )
    list_filter = ['email', 'username']


class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = (
        'is_in_shopping_cart', 'is_favorited', 'publication_date'
    )
    list_filter = ['author', 'name', 'tags']


class IngredientAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    list_filter = ['name']
    search_fields = ['name']


admin.site.register(User, UserAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(RecipeIngredient)
admin.site.register(Follow)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
