from http import HTTPStatus

from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from fpdf import FPDF
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            Shoppingcart, Tag)
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Subscribe, User

from .customixins import (CreateDestroyViewSet, CreateListDestroyViewSet,
                          ListRetriveViewSet)
from .filters import IngredientFilter, RecipeFilter
from .pagination import PageWithLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (CartSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeCartSerializer,
                          RecipePostSerializer, RecipeSerializer,
                          RecipeShortSerializer, SubscribeSerializer,
                          TagSerializer, UserSerializer)


class IngredientViewSet(ListRetriveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny, )
    filter_backends = (DjangoFilterBackend, IngredientFilter)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly, )
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


class TagViewSet(ListRetriveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny, )


class FavoriteViewSet(CreateDestroyViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

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


class SubscribeViewSet(CreateListDestroyViewSet):
    serializer_class = SubscribeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageWithLimitPagination

    def get_queryset(self):
        return Subscribe.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        author_id = self.kwargs.get('author_id')
        author = get_object_or_404(User, id=author_id)
        if author == request.user:
            return Response(
                'Нельзя подписаться на себя',
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
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Shoppingcart.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        try:
            Shoppingcart.objects.create(user=self.request.user, recipe=recipe)
        except IntegrityError:
            return Response(
                'Этот рецепт уже в списке покупок',
                status=HTTPStatus.BAD_REQUEST
            )
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
        response = HttpResponse(
            content_type='application/pdf'
        )
        response['Content-Disposition'] = 'attachment; filename="cart.pdf"'
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Welcome to Python!", ln=1, align="C")
        pdf.output("cart.pdf")
        return response
