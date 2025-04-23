from django.db import models
from inventory.models import Ingredient


class Recipe(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название рецепта")
    description = models.TextField(blank=True, verbose_name="Описание")
    instructions = models.TextField(verbose_name="Пошаговая инструкция")
    steps = models.TextField(verbose_name="Шаги приготовления", default="")
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey('inventory.Ingredient', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.ingredient.name} для {self.recipe.name}"


class Menu(models.Model):
    date = models.DateField(verbose_name="Дата меню")
    recipes = models.ManyToManyField(Recipe, verbose_name="Блюда")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Меню на {self.date}"
