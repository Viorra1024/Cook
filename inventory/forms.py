from django import forms
from .models import Ingredient
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

UNIT_CHOICES = [
    ('kg', 'Килограмм (kg)'),
    ('g', 'Грамм (g)'),
    ('ml', 'Миллилитр (ml)'),
    ('l', 'Литр (l)'),
    ('piece', 'Штука (piece)'),
]


class IngredientForm(forms.ModelForm):
    unit = forms.ChoiceField(choices=UNIT_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Ingredient
        fields = ['name', 'unit', 'quantity', 'min_quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.1}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.1}),  # Поле для порога
        }

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
