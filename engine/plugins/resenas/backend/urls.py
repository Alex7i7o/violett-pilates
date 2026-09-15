from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResenaViewSet

router = DefaultRouter()
router.register(r'resenas', ResenaViewSet, basename='resena')

urlpatterns = [
    path('', include(router.urls)),
]
