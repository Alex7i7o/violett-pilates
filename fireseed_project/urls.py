# Developed by FireSeed - Fueling Innovation
from django.contrib import admin
from django.urls import path, include

from core.views import GoogleLogin

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth endpoints
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # Google OAuth
    path('api/auth/google/', GoogleLogin.as_view(), name='google_login'), 
    path('accounts/', include('allauth.urls')),
    
    # Core API
    path('api/', include('core.urls')),
]
