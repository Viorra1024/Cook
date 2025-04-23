from django.db import models


class Ingredient(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Килограмм (kg)'),
        ('g', 'Грамм (g)'),
        ('ml', 'Миллилитр (ml)'),
        ('l', 'Литр (l)'),
        ('piece', 'Штука (piece)'),
    ]

    name = models.CharField(max_length=255, verbose_name="Название")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, verbose_name="Единица измерения")
    quantity = models.FloatField(verbose_name="Количество", default=0.0)
    min_quantity = models.FloatField(verbose_name="Минимальное количество", default=5.0)  # Добавляем порог

    def __str__(self):
        return f"{self.name} ({self.unit})"


class Supplier(models.Model):
    """Модель поставщика"""
    name = models.CharField(max_length=255, unique=True, verbose_name="Название поставщика")
    contact_info = models.TextField(blank=True, verbose_name="Контактная информация")

    def __str__(self):
        return self.name


class SupplierOrder(models.Model):
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, verbose_name="Поставщик"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    completed = models.BooleanField(default=False, verbose_name="Выполнено")

    def __str__(self):
        status = "✅ Завершён" if self.completed else "⏳ В ожидании"
        return f"Заказ {self.id} - {self.supplier.name} ({status})"


class SupplierOrderItem(models.Model):
    """Модель ингредиентов в заказе"""
    order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    ingredient = models.ForeignKey('inventory.Ingredient', on_delete=models.CASCADE, verbose_name="Ингредиент")
    quantity = models.FloatField(verbose_name="Количество")

    def __str__(self):
        return f"{self.ingredient.name} - {self.quantity}"
