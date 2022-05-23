import django_filters
from rest_framework import filters

from recipes.models import Favorite, Recipe, Shoppingcart


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.CharFilter(field_name='author__id')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        if not value:
            return queryset
        favorites = Favorite.objects.filter(user=self.request.user)
        return queryset.filter(
            pk__in=(favorite.recipe.pk for favorite in favorites)
        )

    def get_is_in_shopping_cart(self, queryset, name, value):
        if not value:
            return queryset
        try:
            carts = Shoppingcart.objects.filter(user=self.request.user)
        except Shoppingcart.DoesNotExist:
            return queryset
        return queryset.filter(
            pk__in=(cart.recipe.pk for cart in carts)
        )


class IngredientFilter(filters.SearchFilter):
    search_param = 'name'
