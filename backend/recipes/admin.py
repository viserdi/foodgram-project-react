from django.conf import settings as s
from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, RecipeTag,
                     Shoppingcart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name',)
    empty_value_display = s.IT_IS_EMPTY


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name',  'measurement_unit')
    search_fields = ('name',)
    empty_value_display = s.IT_IS_EMPTY


class RecipeTagInLine(admin.TabularInline):
    model = RecipeTag
    extra = 0


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeTagInLine, RecipeIngredientInLine,)
    list_display = (
        'author', 'name', 'image', 'text',
        'cooking_time',
    )
    search_fields = ('name',)
    empty_value_display = s.IT_IS_EMPTY


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user',  'recipe')
    search_fields = ('user',)
    empty_value_display = s.IT_IS_EMPTY


@admin.register(Shoppingcart)
class ShoppingcartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    empty_value_display = s.IT_IS_EMPTY
