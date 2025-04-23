from rest_framework import viewsets, status
from .models import Ingredient, SupplierOrder, SupplierOrderItem, Supplier
from .serializers import IngredientSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, redirect, get_object_or_404
from recipes.models import Menu, RecipeIngredient
from celery import shared_task
from django.shortcuts import render
from .forms import IngredientForm
from django.db.models import F, Q, Sum, Count
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

@login_required
def ingredient_list(request):
    ingredients = Ingredient.objects.all()
    return render(request, "inventory/ingredient_list.html", {"ingredients": ingredients})

@login_required
def ingredient_create(request):
    if request.method == "POST":
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ingredient_list')
    else:
        form = IngredientForm()
    return render(request, "inventory/ingredient_form.html", {"form": form})

@login_required
def ingredient_edit(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if request.method == "POST":
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            return redirect('ingredient_list')
    else:
        form = IngredientForm(instance=ingredient)
    return render(request, "inventory/ingredient_form.html", {"form": form})

@login_required
def ingredient_delete(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if request.method == "POST":
        ingredient.delete()
        return redirect('ingredient_list')
    return render(request, "inventory/ingredient_confirm_delete.html", {"ingredient": ingredient})

@login_required
def auto_order_supplier(request):
    """Автоматически создает заказ на недостающие ингредиенты."""
    low_stock_items = Ingredient.objects.filter(quantity__lt=F('min_quantity'))

    if not low_stock_items.exists():
        messages.info(request, "Все ингредиенты в наличии, заказ не требуется")
        return redirect('supplier_orders_list')

    supplier = Supplier.objects.get(name="Default Supplier")  # Получаем объект поставщика
    order = SupplierOrder.objects.create(supplier=supplier)  # Передаем сам объект, а не его имя

    for ingredient in low_stock_items:
        required_quantity = ingredient.min_quantity * 2
        SupplierOrderItem.objects.create(order=order, ingredient=ingredient, quantity=required_quantity)

    messages.success(request, f"Создан заказ #{order.id} на пополнение склада")
    return redirect('supplier_orders_list')

@login_required
def confirm_supplier_order(request):
    """Подтверждает поставку ингредиентов и обновляет склад."""
    order_id = request.GET.get('order_id')

    if not order_id:
        messages.error(request, "Не указан order_id")
        return redirect('supplier_orders_list')

    order = SupplierOrder.objects.filter(id=order_id, completed=False).first()
    if not order:
        messages.error(request, f"Заказ с ID {order_id} не найден или уже подтвержден")
        return redirect('supplier_orders_list')

    for item in order.items.all():
        ingredient = item.ingredient
        ingredient.quantity += item.quantity
        ingredient.save()

    order.completed = True
    order.save()
    messages.success(request, f"Поставка заказа #{order_id} подтверждена")

    return redirect('supplier_orders_list')

@login_required
def supplier_orders_list(request):
    """Отображает список заказов с фильтрацией и сортировкой."""
    query = request.GET.get('q', '')  # Поиск по поставщику
    status = request.GET.get('status', 'all')  # Фильтр по статусу
    sort = request.GET.get('sort', '-created_at')  # Сортировка (по умолчанию новые сверху)

    orders = SupplierOrder.objects.all()

    # Фильтр по статусу
    if status == 'pending':
        orders = orders.filter(completed=False)
    elif status == 'completed':
        orders = orders.filter(completed=True)

    # Фильтр по названию поставщика
    if query:
        orders = orders.filter(Q(supplier__name__icontains=query))

    # Сортировка по дате
    orders = orders.order_by(sort)

    return render(request, "inventory/supplier_orders_list.html", {
        "orders": orders,
        "query": query,
        "status": status,
        "sort": sort
    })

@login_required
def inventory_stats(request):
    """Отображает статистику склада и заказов."""
    # Общий запас ингредиентов
    total_ingredients = Ingredient.objects.aggregate(total_stock=Sum('quantity'))['total_stock'] or 0

    # Недостающие ингредиенты (меньше min_quantity)
    low_stock_ingredients = Ingredient.objects.filter(quantity__lt=F('min_quantity'))

    # Количество заказов у каждого поставщика
    supplier_orders = SupplierOrder.objects.values('supplier__name').annotate(order_count=Count('id'))

    return render(request, "inventory/stats.html", {
        "total_ingredients": total_ingredients,
        "low_stock_ingredients": low_stock_ingredients,
        "supplier_orders": supplier_orders
    })


class IngredientViewSet(LoginRequiredMixin, viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    @action(detail=False, methods=['post'])
    def update_stock_from_supplier(self, request):
        """
        Ожидаемый JSON-формат:
        {
            "supplier": "Fresh Foods Ltd.",
            "products": [
                {"name": "Мука", "quantity": 100, "unit": "kg"},
                {"name": "Сыр", "quantity": 50, "unit": "kg"}
            ]
        }
        """
        supplier__name = request.data.get('supplier', 'Unknown Supplier')
        products = request.data.get('products', [])

        if not products:
            return Response({"error": "Нет данных для обновления склада"}, status=400)

        updated_items = []

        for item in products:
            name, quantity, unit = item['name'], item['quantity'], item['unit']
            ingredient, created = Ingredient.objects.get_or_create(name=name, unit=unit)

            ingredient.quantity += quantity
            ingredient.save()
            updated_items.append({"ingredient": ingredient.name, "new_quantity": ingredient.quantity, "unit": ingredient.unit})

        return Response({
            "status": "Склад обновлен",
            "supplier": supplier__name,
            "updated_items": updated_items
        }, status=200)

    @action(detail=False, methods=['post'])
    def auto_order_supplier(self, request):
        """
        Автоматически создает заказ на недостающие ингредиенты.
        """
        supplier__name = "Default Supplier"  # Можно позже сделать динамическим
        low_stock_items = Ingredient.objects.filter(quantity__lt=10)

        if not low_stock_items:
            return Response({"status": "Все ингредиенты в наличии, заказ не требуется"}, status=200)

        # Создаем заказ с completed=False
        order = SupplierOrder.objects.create(supplier__name=supplier__name, completed=False)

        order_items = []
        for ingredient in low_stock_items:
            required_quantity = 50  # Например, закупаем по 50 единиц, если запасы низкие
            SupplierOrderItem.objects.create(order=order, ingredient=ingredient, quantity=required_quantity)
            order_items.append({
                "ingredient": ingredient.name,
                "ordered_quantity": required_quantity,
                "unit": ingredient.unit
            })

        return Response({
            "status": "Создан заказ поставщику",
            "supplier": supplier__name,
            "order_id": order.id,
            "order_items": order_items
        }, status=201)

    @action(detail=False, methods=['post'], url_path='confirm_delivery')
    def confirm_delivery(self, request):
        """
        Подтверждение поставки ингредиентов по заказу.
        """
        order_id = request.data.get('order_id')
        order = get_object_or_404(SupplierOrder, id=order_id, completed=False)

        updated_items = []
        for item in order.supplierorderitem_set.all():  # Исправлено!
            ingredient = item.ingredient
            ingredient.quantity += item.quantity
            ingredient.save()
            updated_items.append({
                "ingredient": ingredient.name,
                "new_quantity": ingredient.quantity,
                "unit": ingredient.unit
            })

        order.completed = True
        order.save()

        return Response({
            "status": "Поставка подтверждена",
            "order_id": order_id,
            "updated_items": updated_items
        }, status=200)

    @action(detail=False, methods=['post'], url_path='confirm_supplier_order')
    def confirm_supplier_order(self, request):
        """
        Подтверждает доставку заказа от поставщика и обновляет склад.
        Если есть отложенные меню из-за нехватки ингредиентов, они активируются.
        """
        order_id = request.data.get('order_id')
        order = get_object_or_404(SupplierOrder, id=order_id, completed=False)

        updated_items = []

        for item in order.supplierorderitem_set.all():
            ingredient = item.ingredient
            ingredient.quantity += item.quantity
            ingredient.save()
            updated_items.append({
                "ingredient": ingredient.name,
                "new_quantity": ingredient.quantity,
                "unit": ingredient.unit
            })

        order.completed = True
        order.save()

        # Проверяем, можно ли теперь активировать отложенные меню
        menus_to_activate = []
        for menu in Menu.objects.filter(date__gte=now().date()):
            can_activate = True

            for recipe in menu.recipes.all():
                for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
                    ingredient = recipe_ingredient.ingredient
                    required_quantity = recipe_ingredient.quantity

                    if ingredient.quantity < required_quantity:
                        can_activate = False
                        break

                if not can_activate:
                    break

            if can_activate:
                menus_to_activate.append(menu)
                for recipe in menu.recipes.all():
                    for recipe_ingredient in RecipeIngredient.objects.filter(recipe=recipe):
                        ingredient = recipe_ingredient.ingredient
                        ingredient.quantity -= recipe_ingredient.quantity
                        ingredient.save()

        return Response({
            "status": "Заказ подтвержден, склад обновлен",
            "updated_items": updated_items,
            "activated_menus": [{"id": menu.id, "date": menu.date} for menu in menus_to_activate]
        }, status=status.HTTP_200_OK)


@action(detail=False, methods=['get'], url_path='check_low_stock')
def check_low_stock(self, request):
    """
    Проверяет склад на наличие ингредиентов с низким уровнем запасов.
    Если ингредиентов критически мало, создается заказ у поставщиков.
    """
    low_stock_items = []
    critical_stock_items = []

    for ingredient in Ingredient.objects.all():
        if ingredient.quantity < 10:  # Если запас < 10, отправляем уведомление
            low_stock_items.append({
                "ingredient": ingredient.name,
                "quantity": ingredient.quantity,
                "unit": ingredient.unit
            })
        if ingredient.quantity < 5:  # Если запас < 5, автоматически создаем заказ
            critical_stock_items.append(ingredient)

    if critical_stock_items:
        order = SupplierOrder.objects.create(supplier__name="Auto Supplier", completed=False)
        for ingredient in critical_stock_items:
            SupplierOrderItem.objects.create(order=order, ingredient=ingredient, quantity=50)

        return Response({
            "status": "Обнаружены критически низкие запасы, создан заказ",
            "order_id": order.id,
            "low_stock_items": low_stock_items
        }, status=status.HTTP_202_ACCEPTED)

    return Response({
        "status": "Проверка завершена",
        "low_stock_items": low_stock_items
    }, status=status.HTTP_200_OK)
