from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServicioEsteticaViewSet

router = DefaultRouter()
router.register(r'servicios', ServicioEsteticaViewSet, basename='estetica-servicios')

urlpatterns = [
    path('', include(router.urls)),
]
