from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=50,
        unique=True,
    )
    color = ColorField()
    slug = models.SlugField(
        'Слаг',
        unique=True,
    )

    class Meta:
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name[:15]


class Ingredient(models.Model):
    name = models.CharField(
        'Наименование',
        max_length=100,
    )

    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=20,
    )

    class Meta:
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name[:15]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='автор',
        on_delete=models.CASCADE,
        related_name='recipe_author'
    )
    name = models.CharField(
        'Название',
        max_length=200,
    )
    image = models.ImageField('Картинка',)
    text = models.TextField('Описание',)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes',
        blank=False,
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='тэги'
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(1)],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:15]


class RecipeTag(models.Model):
    tag = models.ForeignKey(
        Tag,
        verbose_name='тэг рецепта',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredient'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipe_ingredient',
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        default=1,
    )


class Shoppingcart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор списка',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепты',
        related_name='cartrecipe'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user.username} -> {self.recipe.name}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.DO_NOTHING,
        related_name='favoriterecipe'
    )

    class Meta:
        verbose_name = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} likes {self.recipe}'
