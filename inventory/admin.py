from django.contrib import admin
from .models import Supplier, SupplierOrder, SupplierOrderItem, Ingredient


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_info')
    search_fields = ('name',)


class SupplierOrderItemInline(admin.TabularInline):
    model = SupplierOrderItem
    extra = 1


@admin.register(SupplierOrder)
class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'created_at', 'completed')
    list_filter = ('completed', 'supplier')
    search_fields = ('supplier__name',)
    inlines = [SupplierOrderItemInline]


@admin.register(SupplierOrderItem)
class SupplierOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'ingredient', 'quantity')
    search_fields = ('order__id', 'ingredient__name')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'unit')
    search_fields = ('name',)
    list_filter = ('unit',)

