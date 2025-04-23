from rest_framework import serializers
from .models import Recipe, RecipeIngredient, Menu
from inventory.models import Ingredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.ReadOnlyField(source='ingredient.name')

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'ingredient_name', 'quantity']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'description', 'instructions', 'ingredients']


class MenuSerializer(serializers.ModelSerializer):
    recipes = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        many=True
    )

    class Meta:
        model = Menu
        fields = ['id', 'date', 'recipes', 'created_at']