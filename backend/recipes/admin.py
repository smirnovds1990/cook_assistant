from django.contrib import admin

from .models import Follow, Ingridient, Recipe, RecipeIngridient, Tag, User


class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('is_subscribed', )
    list_filter = ['email', 'username']


class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = (
        'is_in_shopping_cart', 'is_favorited', 'publication_date'
    )
    list_filter = ['author', 'name', 'tags']


class IngridientAdmin(admin.ModelAdmin):
    readonly_fields = ['id']
    list_filter = ['name']
    search_fields = ['name']


admin.site.register(User, UserAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingridient, IngridientAdmin)
admin.site.register(Tag)
admin.site.register(RecipeIngridient)
admin.site.register(Follow)
