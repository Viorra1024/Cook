from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RecipeViewSet, MenuViewSet, recipe_list, recipe_detail,
    recipe_create, recipe_edit, recipe_delete, menu_list, menu_view,
    calculate_ingredients, remove_from_menu, cook_recipe, cook_recipe_from_menu
                    )
router = DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'menu', MenuViewSet)

urlpatterns = [
    path('recipes/<int:pk>/check_ingredients/', RecipeViewSet.as_view({'get': 'check_ingredients'}), name='check-ingredients'),
    path('recipes/<int:pk>/calculate_ingredients/', RecipeViewSet.as_view({'get': 'calculate_ingredients'}), name='calculate-ingredients'),
    path('recipes/<int:pk>/prepare/', RecipeViewSet.as_view({'post': 'prepare_recipe'}), name='prepare-recipe'),
    path('recipes/<int:pk>/shopping_list/', RecipeViewSet.as_view({'get': 'generate_shopping_list'}), name='generate-shopping-list'),
    path('menu/generate_weekly/', MenuViewSet.as_view({'post': 'generate_weekly_menu'}), name='generate-weekly-menu'),
    path('recipes/', recipe_list, name='recipe_list'),
    path('recipes/<int:recipe_id>/', recipe_detail, name='recipe_detail'),
    path('calculate_ingredients/', calculate_ingredients, name='calculate_ingredients'),
    path('recipes/add/', recipe_create, name='recipe_create'),
    path('recipes/<int:recipe_id>/edit/', recipe_edit, name='recipe_edit'),
    path('recipes/<int:recipe_id>/delete/', recipe_delete, name='recipe_delete'),
    path('menu/', menu_view, name='menu'),
    path('menu/', menu_list, name='menu_list'),
    path('cook/<int:menu_id>/<int:recipe_id>/', cook_recipe_from_menu, name='cook_recipe_from_menu'),
    path('menu/remove/<int:recipe_id>/', remove_from_menu, name='remove_from_menu'),
    path('', include(router.urls)),
]

