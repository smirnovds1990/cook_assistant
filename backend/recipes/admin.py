from django.contrib import admin

from .models import Ingridient, Recipe, Tag, User


class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('is_subscribed', )


class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = ('is_in_shopping_cart', 'is_favorited')


admin.site.register(User, UserAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingridient)
admin.site.register(Tag)
