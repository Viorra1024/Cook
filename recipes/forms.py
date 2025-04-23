from django import forms
from .models import Recipe, RecipeIngredient, Ingredient


class RecipeIngredientForm(forms.ModelForm):
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Выберите ингредиент"
    )

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.1, 'placeholder': 'Введите количество'}),
        }


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['name', 'description', 'steps']
