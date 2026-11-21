# Developed by FireSeed - Fueling Innovation
from django.contrib import admin
from django.urls import path, include
from .plugin_loader import get_plugin_urls

from core.views import GoogleLogin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    
    # Core API (includes /api/auth/ with ThrottledLoginView, registration, etc.)
    path('api/', include('core.urls')),
]

# Inyectar URLs de los plugins activos
for route, module in get_plugin_urls():
    urlpatterns.append(path(route, include(module)))
