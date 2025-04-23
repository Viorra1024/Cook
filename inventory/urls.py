from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IngredientViewSet, ingredient_list, ingredient_create, ingredient_edit,
    ingredient_delete, auto_order_supplier, confirm_supplier_order,
    supplier_orders_list, inventory_stats
)

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path('ingredients/check_low_stock/', IngredientViewSet.as_view({'get': 'check_low_stock'}), name='check-low-stock'),
    path('ingredients/', ingredient_list, name='ingredient_list'),
    path('ingredients/add/', ingredient_create, name='ingredient_create'),
    path('ingredients/auto_order/', auto_order_supplier, name='auto_order_supplier'),
    path('orders/', supplier_orders_list, name='supplier_orders_list'),
    path('ingredients/confirm_delivery/', confirm_supplier_order, name='confirm_delivery'),
    path('stats/', inventory_stats, name='inventory_stats'),
    path('ingredients/<int:ingredient_id>/edit/', ingredient_edit, name='ingredient_edit'),
    path('ingredients/<int:ingredient_id>/delete/', ingredient_delete, name='ingredient_delete'),
    path('', include(router.urls)),
]

