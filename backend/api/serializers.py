from django.contrib.auth.hashers import make_password
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, Shoppingcart, Tag)
from rest_framework import serializers
from users.models import Subscribe, User


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        import base64
        import uuid

        import six
        from django.core.files.base import ContentFile

        if isinstance(data, six.string_types):
            if 'data:' in data and ';base64,' in data:
                header, data = data.split(';base64,')

            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            file_name = str(uuid.uuid4())[:12]
            file_extension = self.get_file_extension(file_name, decoded_file)
            complete_file_name = "%s.%s" % (file_name, file_extension, )
            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        return "jpg" if extension == "jpeg" else extension


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientShortSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'password',
            'first_name', 'last_name', 'is_subscribed'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = (
            make_password(validated_data.pop('password'))
        )
        return super().create(validated_data)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return(
            Subscribe.objects.filter(
                user=request.user,
                author__id=obj.id
            ).exists()
            and request.user.is_authenticated
        )


class SubscribeSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request:
            return True
        return(
            Subscribe.objects.filter(
                user=request.user,
                author__id=obj.author.id
            ).exists()
            and request.user.is_authenticated
        )

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj):
        try:
            recipes_limit = int(
                self.context.get('request').query_params['recipes_limit']
            )
            recipes = Recipe.objects.filter(author=obj.author)[:recipes_limit]
        except Exception:
            recipes = Recipe.objects.filter(author=obj.author)
        serializer = RecipeShortSerializer(recipes, many=True,)
        return serializer.data


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    author = UserSerializer(many=False)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredient'
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return(
            Favorite.objects.filter(
                user=request.user,
                recipe__id=obj.id
            ).exists()
            and request.user.is_authenticated
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return(
            Shoppingcart.objects.filter(
                user=request.user,
                recipe__id=obj.id
            ).exists()
            and request.user.is_authenticated
        )


class RecipePostSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=False)
    ingredients = RecipeIngredientShortSerializer(
        source='recipe_ingredient',
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserSerializer(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'ingredients', 'tags', 'cooking_time',
            'is_in_shopping_cart', 'is_favorited'
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return(
            Shoppingcart.objects.filter(
                user=request.user,
                recipe__id=obj.id
            ).exists()
            and request.user.is_authenticated
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return(
            Favorite.objects.filter(
                user=request.user,
                recipe__id=obj.id
            ).exists()
            and request.user.is_authenticated
        )

    def validate_ingredients(self, value):
        ingredients_list = []
        ingredients = value
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество должно быть равным или больше 1!')
            check_id = ingredient['ingredient']['id']
            check_ingredient = Ingredient.objects.filter(id=check_id)
            if not check_ingredient.exists():
                raise serializers.ValidationError(
                    'Ингредиента нет в базе!')
            if check_ingredient in ingredients_list:
                raise serializers.ValidationError(
                    'Продукты не должны повторяться!')
            ingredients_list.append(check_ingredient)
        return value

    def add_tags_and_ingredients(self, tags, ingredients, recipe):
        for tag in tags:
            recipe.tags.add(tag)
            recipe.save()
        for ingredient in ingredients:
            if not RecipeIngredient.objects.filter(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe).exists():
                ingredientrecipe = RecipeIngredient.objects.create(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe)
                ingredientrecipe.amount = ingredient['amount']
                ingredientrecipe.save()
            else:
                RecipeIngredient.objects.filter(
                    recipe=recipe).delete()
                recipe.delete()
                raise serializers.ValidationError(
                    'Данные продукты повторяются в рецепте!')
        return recipe

    def create(self, validated_data):
        author = validated_data.get('author')
        tags = validated_data.pop('tags')
        name = validated_data.get('name')
        image = validated_data.get('image')
        text = validated_data.get('text')
        cooking_time = validated_data.get('cooking_time')
        ingredients = validated_data.pop('recipe_ingredient')
        recipe = Recipe.objects.create(
            author=author,
            name=name,
            image=image,
            text=text,
            cooking_time=cooking_time,
        )
        return self.add_tags_and_ingredients(tags, ingredients, recipe)

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredient')
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        instance = self.add_tags_and_ingredients(
            tags, ingredients, instance)
        super().update(instance, validated_data)
        instance.save()
        return instance


class RecipeCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shoppingcart
        fields = '__all__'
