from http import HTTPStatus

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, Tag
from users.models import Subscribe, User

from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipePostSerializer, RecipeSerializer,
                          RecipeShortSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    http_method_names = ['get']


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipePostSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    http_method_names = ('get',)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
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
        get_object_or_404(Favorite, user=self.request.user, recipe=recipe).delete()
        return Response(status=HTTPStatus.NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class SubscribeViewSet(viewsets.ModelViewSet):
    serializer_class = SubscribeSerializer

    def get_queryset(self):
        queryset = Subscribe.objects.filter(user=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        author_id = self.kwargs.get('author_id')
        author = get_object_or_404(User, id=author_id)
        Subscribe.objects.create(author=author, user=self.request.user)
        subscription = get_object_or_404(Subscribe, author=author, user=self.request.user)
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
