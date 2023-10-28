from django import forms
from django.core.exceptions import ValidationError

from recipes.models import Recipe, Tag


class RecipeForm(forms.ModelForm):

    class Meta:
        model = Recipe
        fields = '__all__'

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            raise ValidationError('У рецепта должно быть изображение.')
        return image


class TagForm(forms.ModelForm):

    class Meta:
        model = Tag
        fields = '__all__'

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Tag.objects.filter(name=name).exists():
            raise ValidationError('Тег с таким именем уже существует.')
        return name

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if Tag.objects.filter(slug=slug).exists():
            raise ValidationError('Slug с таким именем уже существует.')
        return slug
