from django.contrib import admin
from django.urls import path, include
from recipes.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('', home, name='home'),  # Главная страница
    path('', include('recipes.urls')),
    path('', include('inventory.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('recipes.urls')),
]
