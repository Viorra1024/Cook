from rest_framework import viewsets, status
from .models import Recipe, RecipeIngredient, Menu
from inventory.models import Ingredient
from .serializers import RecipeSerializer, RecipeIngredient, MenuSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from inventory.models import Ingredient, SupplierOrder, SupplierOrderItem
from datetime import datetime, timedelta, date
from django.utils.timezone import now
from django.shortcuts import render, get_object_or_404, redirect
from .forms import RecipeForm, RecipeIngredientForm
from django.forms import modelformset_factory, inlineformset_factory
from django.db.models import Sum
from django.contrib import messages
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


@login_required
def recipe_list(request):
    recipes = Recipe.objects.all()
    return render(request, "recipes/recipe_list.html", {"recipes": recipes})

@login_required
def home(request):
    return render(request, "home.html")

@login_required
def menu_list(request):
    menus = Menu.objects.all().order_by('-date')
    return render(request, "recipes/menu_list.html", {"menus": menus})

@login_required
def menu_view(request):
    """Отображает меню на день и позволяет добавлять рецепты."""
    today = date.today()

    # Получаем меню на сегодня (если несколько — берем первое)
    menu = Menu.objects.filter(date=today).first()

    # Если меню не существует, создаем новое
    if not menu:
        menu = Menu.objects.create(date=today)

    recipes = Recipe.objects.all()

    if request.method == "POST":
        recipe_id = request.POST.get("recipe_id")
        if recipe_id:
            recipe = Recipe.objects.get(id=recipe_id)
            menu.recipes.add(recipe)

    return render(request, "recipes/menu.html", {
        "recipes": recipes,
        "menu": menu
    })

@login_required
def remove_from_menu(request, recipe_id):
    """Удаляет рецепт из меню на сегодня"""
    today = date.today()
    menu = Menu.objects.filter(date=today).first()

    if menu:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        menu.recipes.remove(recipe)

    return redirect('menu')

@login_required
def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)  # Получаем ингредиенты с их количеством
    steps = recipe.steps.split('.') if recipe.steps else []  # Разбиваем шаги приготовления

    return render(request, "recipes/recipe_detail.html", {
        "recipe": recipe,
        "recipe_ingredients": recipe_ingredients,
        "steps": steps
    })

@login_required
def recipe_create(request):
    RecipeIngredientFormSet = inlineformset_factory(Recipe, RecipeIngredient, form=RecipeIngredientForm, extra=3, can_delete=True)

    if request.method == "POST":
        form = RecipeForm(request.POST)
        formset = RecipeIngredientFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            recipe = form.save()
            formset.instance = recipe  # Связываем ингредиенты с рецептом
            formset.save()
            return redirect('recipe_list')
    else:
        form = RecipeForm()
        formset = RecipeIngredientFormSet()

    return render(request, "recipes/recipe_form.html", {"form": form, "formset": formset})

@login_required
def recipe_edit(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    RecipeIngredientFormSet = inlineformset_factory(
        Recipe, RecipeIngredient, form=RecipeIngredientForm, extra=1, can_delete=True  # Теперь можно добавлять ингредиенты
    )

    if request.method == "POST":
        form = RecipeForm(request.POST, instance=recipe)
        formset = RecipeIngredientFormSet(request.POST, instance=recipe)

        if form.is_valid() and formset.is_valid():
            print("✅ Форма валидна, сохраняем данные")
            recipe = form.save()
            formset.instance = recipe
            formset.save()
            return redirect('recipe_list')
        else:
            print("❌ Ошибка валидации формы!")
            print("Ошибки формы:", form.errors)
            print("Ошибки formset:", formset.errors)

    else:
        form = RecipeForm(instance=recipe)
        formset = RecipeIngredientFormSet(instance=recipe)

    return render(request, "recipes/recipe_form.html", {"form": form, "formset": formset})

@login_required
def recipe_delete(request, recipe_id):
    recipe = Recipe.objects.get(id=recipe_id)
    if request.method == "POST":
        recipe.delete()
        return redirect('recipe_list')
    return render(request, "recipes/recipe_confirm_delete.html", {"recipe": recipe})

@login_required
def calculate_ingredients(request):
    """Рассчитывает необходимые ингредиенты для текущего меню и автоматически заказывает недостающие"""
    today = date.today()
    menu = Menu.objects.filter(date=today).first()

    if not menu or not menu.recipes.exists():
        return render(request, "recipes/calculate_ingredients.html", {"error": "В меню нет рецептов"})

    required_ingredients = {}
    low_stock_items = []

    for recipe in menu.recipes.all():
        for recipe_ingredient in recipe.recipeingredient_set.all():
            ing = recipe_ingredient.ingredient
            quantity_needed = recipe_ingredient.quantity

            if ing.name in required_ingredients:
                required_ingredients[ing.name]["quantity_needed"] += quantity_needed
            else:
                required_ingredients[ing.name] = {
                    "unit": ing.unit,
                    "quantity_needed": quantity_needed,
                    "quantity_available": ing.quantity
                }

            # Проверяем, хватает ли ингредиента
            if ing.quantity < quantity_needed:
                low_stock_items.append(ing)

    # Автоматический заказ, если ингредиентов недостаточно
    if low_stock_items:
        order = SupplierOrder.objects.create(supplier_name="Default Supplier")

        for ingredient in low_stock_items:
            required_quantity = max(ingredient.min_quantity * 2, 50)  # Заказываем минимум x2 от порога
            SupplierOrderItem.objects.create(order=order, ingredient=ingredient, quantity=required_quantity)

    return render(request, "recipes/calculate_ingredients.html", {
        "required_ingredients": required_ingredients,
        "low_stock_items": low_stock_items
    })

@login_required
def cook_recipe(request, menu_id):
    menu = get_object_or_404(Menu, id=menu_id)
    recipe = menu.recipe
    insufficient = []

    for ri in RecipeIngredient.objects.filter(recipe=recipe):
        if ri.ingredient.quantity < ri.quantity:
            insufficient.append(f"{ri.ingredient.name} (нужно: {ri.quantity}, есть: {ri.ingredient.quantity})")

    if insufficient:
        messages.error(request, f"Недостаточно ингредиентов: {', '.join(insufficient)}")
    else:
        for ri in RecipeIngredient.objects.filter(recipe=recipe):
            ri.ingredient.quantity -= ri.quantity
            ri.ingredient.save()
        messages.success(request, f"Рецепт «{recipe.name}» успешно приготовлен. Ингредиенты обновлены.")

    return redirect('menu_list')

@login_required
def cook_recipe_from_menu(request, menu_id, recipe_id):
    menu = get_object_or_404(Menu, id=menu_id)
    recipe = get_object_or_404(Recipe, id=recipe_id)

    if recipe not in menu.recipes.all():
        messages.error(request, "Этот рецепт не входит в выбранное меню.")
        return redirect('menu_list')

    insufficient = []
    for ri in RecipeIngredient.objects.filter(recipe=recipe):
        if Decimal(ri.ingredient.quantity) < ri.quantity:
            insufficient.append(f"{ri.ingredient.name} (нужно: {ri.quantity}, есть: {ri.ingredient.quantity})")

    if insufficient:
        messages.error(request, f"❌ Недостаточно ингредиентов: {', '.join(insufficient)}")
    else:
        for ri in RecipeIngredient.objects.filter(recipe=recipe):
            ri.ingredient.quantity = Decimal(ri.ingredient.quantity) - Decimal(ri.quantity)
            ri.ingredient.quantity = ri.ingredient.quantity.quantize(Decimal("0.01"))  # Округление до 2 знаков
            ri.ingredient.save()
        messages.success(request, f"✅ Рецепт «{recipe.name}» приготовлен. Ингредиенты списаны.")

    return redirect('menu_list')


class RecipeViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    @action(detail=True, methods=['get'])
    def check_ingredients(self, request, pk=None):
        recipe = self.get_object()
        missing_ingredients = []

        for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
            ingredient = recipe_ingredient.ingredient
            required_quantity = recipe_ingredient.quantity

            if ingredient.quantity < required_quantity:
                missing_ingredients.append({
                    "ingredient": ingredient.name,
                    "required": required_quantity,
                    "available": ingredient.quantity
                })

        if missing_ingredients:
            return Response({"status": "Недостаточно ингредиентов", "missing": missing_ingredients}, status=400)

        return Response({"status": "Все ингредиенты в наличии"}, status=200)

    @action(detail=True, methods=['get'])
    def calculate_ingredients(self, request, pk=None):
        recipe = self.get_object()
        try:
            servings = int(request.query_params.get('servings', 1))
        except ValueError:
            return Response({"error": "Параметр servings должен быть числом"}, status=400)

        missing_ingredients = []
        required_ingredients = []

        for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
            ingredient = recipe_ingredient.ingredient
            required_quantity = recipe_ingredient.quantity * servings

            required_ingredients.append({
                "ingredient": ingredient.name,
                "required": required_quantity,
                "available": ingredient.quantity,
                "unit": ingredient.unit
            })

            if ingredient.quantity < required_quantity:
                missing_ingredients.append({
                    "ingredient": ingredient.name,
                    "required": required_quantity,
                    "available": ingredient.quantity,
                    "unit": ingredient.unit
                })

        response_data = {
            "recipe": recipe.name,
            "servings": servings,
            "required_ingredients": required_ingredients,
            "missing_ingredients": missing_ingredients,
            "status": "Недостаточно ингредиентов" if missing_ingredients else "Все ингредиенты в наличии"
        }

        return Response(response_data, status=200)

    @action(detail=True, methods=['post'])
    def prepare_recipe(self, request, pk=None):
        recipe = self.get_object()
        try:
            servings = int(request.data.get('servings', 1))
        except ValueError:
            return Response({"error": "Параметр servings должен быть числом"}, status=400)

        missing_ingredients = []
        update_list = []

        # Проверяем наличие всех ингредиентов
        for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
            ingredient = recipe_ingredient.ingredient
            required_quantity = recipe_ingredient.quantity * servings

            if ingredient.quantity < required_quantity:
                missing_ingredients.append({
                    "ingredient": ingredient.name,
                    "required": required_quantity,
                    "available": ingredient.quantity,
                    "unit": ingredient.unit
                })
            else:
                update_list.append((ingredient, required_quantity))

        if missing_ingredients:
            return Response({
                "status": "Недостаточно ингредиентов",
                "missing": missing_ingredients
            }, status=400)

        # Если ингредиентов хватает – обновляем склад
        for ingredient, required_quantity in update_list:
            ingredient.quantity -= required_quantity
            ingredient.save()

        return Response({
            "status": "Ингредиенты списаны",
            "recipe": recipe.name,
            "servings": servings
        }, status=200)

    @action(detail=True, methods=['get'])
    def generate_shopping_list(self, request, pk=None):
        recipe = self.get_object()
        try:
            servings = int(request.query_params.get('servings', 1))
        except ValueError:
            return Response({"error": "Параметр servings должен быть числом"}, status=400)

        shopping_list = []

        for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
            ingredient = recipe_ingredient.ingredient
            required_quantity = recipe_ingredient.quantity * servings

            if ingredient.quantity < required_quantity:
                shopping_list.append({
                    "ingredient": ingredient.name,
                    "needed": required_quantity - ingredient.quantity,
                    "unit": ingredient.unit
                })

        if not shopping_list:
            return Response({"status": "Все ингредиенты в наличии, покупки не требуются"}, status=200)

        return Response({"status": "Требуется закупка", "shopping_list": shopping_list}, status=200)


class MenuViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    queryset = Menu.objects.all().order_by('-date')
    serializer_class = MenuSerializer

    def create(self, request, *args, **kwargs):
        """
        Проверка ингредиентов перед добавлением в меню.
        Если ингредиентов достаточно, они резервируются.
        """
        recipes = request.data.get('recipes', [])
        missing_ingredients = []
        reserved_ingredients = []

        for recipe_id in recipes:
            try:
                recipe = Recipe.objects.get(id=recipe_id)
            except Recipe.DoesNotExist:
                return Response({"error": f"Рецепт с ID {recipe_id} не найден"}, status=status.HTTP_400_BAD_REQUEST)

            for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
                ingredient = recipe_ingredient.ingredient
                required_quantity = recipe_ingredient.quantity

                if ingredient.quantity < required_quantity:
                    missing_ingredients.append({
                        "ingredient": ingredient.name,
                        "required": required_quantity,
                        "available": ingredient.quantity,
                        "unit": ingredient.unit
                    })
                else:
                    reserved_ingredients.append((ingredient, required_quantity))

        if missing_ingredients:
            return Response({
                "status": "Недостаточно ингредиентов",
                "missing_ingredients": missing_ingredients
            }, status=status.HTTP_400_BAD_REQUEST)

        # Если ингредиентов хватает, резервируем их
        for ingredient, required_quantity in reserved_ingredients:
            ingredient.quantity -= required_quantity
            ingredient.save()

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        При удалении меню ингредиенты возвращаются на склад.
        """
        menu = self.get_object()
        recipes = menu.recipes.all()

        for recipe in recipes:
            for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
                ingredient = recipe_ingredient.ingredient
                ingredient.quantity += recipe_ingredient.quantity  # Возвращаем зарезервированные ингредиенты
                ingredient.save()

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='generate_weekly')
    def generate_weekly_menu(self, request):
        """
        Автоматически генерирует меню на 7 дней вперед, проверяя наличие ингредиентов.
        """
        start_date = now().date()
        end_date = start_date + timedelta(days=6)
        available_recipes = Recipe.objects.all()
        generated_menus = []

        if not available_recipes.exists():
            return Response({"error": "Нет доступных рецептов"}, status=status.HTTP_400_BAD_REQUEST)

        for i in range(7):
            day = start_date + timedelta(days=i)
            selected_recipes = []
            reserved_ingredients = []

            for recipe in available_recipes:
                missing_ingredients = []
                temp_reserve = []

                for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
                    ingredient = recipe_ingredient.ingredient
                    required_quantity = recipe_ingredient.quantity

                    if ingredient.quantity < required_quantity:
                        missing_ingredients.append({
                            "ingredient": ingredient.name,
                            "required": required_quantity,
                            "available": ingredient.quantity,
                            "unit": ingredient.unit
                        })
                    else:
                        temp_reserve.append((ingredient, required_quantity))

                if not missing_ingredients:
                    selected_recipes.append(recipe)
                    reserved_ingredients.extend(temp_reserve)

                    if len(selected_recipes) >= 3:  # Ограничиваем 3 блюда в день
                        break

            if selected_recipes:
                # Резервируем ингредиенты
                for ingredient, required_quantity in reserved_ingredients:
                    ingredient.quantity -= required_quantity
                    ingredient.save()

                menu = Menu.objects.create(date=day)
                menu.recipes.set(selected_recipes)
                generated_menus.append({"date": day, "recipes": [r.id for r in selected_recipes]})

        return Response({
            "status": "Меню на неделю сгенерировано",
            "menus": generated_menus
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='generate_weekly')
    def generate_weekly_menu(self, request):
        """
        Автоматически генерирует меню на 7 дней вперед.
        Если не хватает ингредиентов, создается заказ у поставщика.
        """
        start_date = now().date()
        available_recipes = Recipe.objects.all()
        generated_menus = []
        missing_ingredients = {}

        if not available_recipes.exists():
            return Response({"error": "Нет доступных рецептов"}, status=status.HTTP_400_BAD_REQUEST)

        for i in range(7):
            day = start_date + timedelta(days=i)
            selected_recipes = []
            reserved_ingredients = []
            temp_missing = {}

            for recipe in available_recipes:
                temp_reserve = []
                for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
                    ingredient = recipe_ingredient.ingredient
                    required_quantity = recipe_ingredient.quantity

                    if ingredient.quantity < required_quantity:
                        temp_missing[ingredient.name] = {
                            "required": required_quantity,
                            "available": ingredient.quantity,
                            "unit": ingredient.unit
                        }
                    else:
                        temp_reserve.append((ingredient, required_quantity))

                if not temp_missing:
                    selected_recipes.append(recipe)
                    reserved_ingredients.extend(temp_reserve)

                    if len(selected_recipes) >= 3:  # Ограничиваем 3 блюда в день
                        break

            if temp_missing:
                missing_ingredients.update(temp_missing)
            else:
                # Резервируем ингредиенты
                for ingredient, required_quantity in reserved_ingredients:
                    ingredient.quantity -= required_quantity
                    ingredient.save()

                menu = Menu.objects.create(date=day)
                menu.recipes.set(selected_recipes)
                generated_menus.append({"date": day, "recipes": [r.id for r in selected_recipes]})

        if missing_ingredients:
            # Создаем заказ у поставщиков
            order = SupplierOrder.objects.create(supplier_name="Auto Supplier", completed=False)
            for ingredient_name, data in missing_ingredients.items():
                ingredient, created = Ingredient.objects.get_or_create(name=ingredient_name, unit=data["unit"])
                SupplierOrderItem.objects.create(order=order, ingredient=ingredient,
                                                 quantity=data["required"] - data["available"])

            return Response({
                "status": "Недостаточно ингредиентов, создан заказ у поставщика",
                "missing_ingredients": missing_ingredients,
                "order_id": order.id
            }, status=status.HTTP_202_ACCEPTED)

        return Response({
            "status": "Меню на неделю сгенерировано",
            "menus": generated_menus
        }, status=status.HTTP_201_CREATED)