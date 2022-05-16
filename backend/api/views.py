from http import HTTPStatus

from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            Shoppingcart, Tag)
from users.models import Subscribe, User

from .filters import RecipeFilter
from .pagination import PageWithLimitPagination
from .serializers import (CartSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeCartSerializer,
                          RecipePostSerializer, RecipeSerializer,
                          RecipeShortSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny, )
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('^name',)
    http_method_names = ['get']


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (permissions.AllowAny,)
    filter_class = RecipeFilter
    filter_backends = (DjangoFilterBackend, )
    pagination_class = PageWithLimitPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        else:
            return RecipePostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny, )
    http_method_names = ('get',)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('post', 'delete')

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        Favorite.objects.create(user=self.request.user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe, many=False)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=recipe
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageWithLimitPagination


class SubscribeViewSet(viewsets.ModelViewSet):
    serializer_class = SubscribeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageWithLimitPagination

    def get_queryset(self):
        queryset = Subscribe.objects.filter(user=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        author_id = self.kwargs.get('author_id')
        author = get_object_or_404(User, id=author_id)
        if author == request.user:
            return Response(
                'Нельзя полписаться на себя',
                status=HTTPStatus.BAD_REQUEST
            )
        try:
            Subscribe.objects.create(author=author, user=self.request.user)
        except IntegrityError:
            return Response(
                'Вы уже подписаны на данного автора',
                status=HTTPStatus.BAD_REQUEST
            )
        subscription = get_object_or_404(
            Subscribe,
            author=author,
            user=self.request.user
        )
        serializer = SubscribeSerializer(subscription, many=False)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        author_id = self.kwargs.get('author_id')
        author = get_object_or_404(User, id=author_id)
        get_object_or_404(
            Subscribe,
            author=author,
            user=self.request.user
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    queryset = Shoppingcart.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        Shoppingcart.objects.create(user=self.request.user, recipe=recipe)
        serializer = RecipeCartSerializer(recipe, many=False)
        return Response(data=serializer.data, status=HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(
            Shoppingcart,
            user=self.request.user,
            recipe=recipe
        ).delete()
        return Response(status=HTTPStatus.NO_CONTENT)


class DownloadShoppingCartViewSet(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        carts = Shoppingcart.objects.filter(user=user)
        recipes = [cart.recipe for cart in carts]
        cart_dict = {}
        for recipe in recipes:
            for ingredient in recipe.ingredients.all():
                amount = get_object_or_404(
                    RecipeIngredient,
                    recipe=recipe,
                    ingredient=ingredient
                ).amount
                if ingredient.name not in cart_dict:
                    cart_dict[ingredient.name] = amount
                else:
                    cart_dict[ingredient.name] += amount
        content = ''
        for item in cart_dict:
            measurement_unit = get_object_or_404(
                Ingredient,
                name=item
            ).measurement_unit
            content += f'{item} -- {cart_dict[item]} {measurement_unit}\n'
        print(content)
        response = HttpResponse(
            content, content_type='text/plain,charset=utf8'
        )
        response['Content-Disposition'] = 'attachment; filename="cart.txt"'
        return response
