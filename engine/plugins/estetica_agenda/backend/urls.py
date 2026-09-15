from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DisponibilidadDiaViewSet, ReservaEsteticaViewSet, get_disponibilidad

router = DefaultRouter()
router.register(r'config-dias', DisponibilidadDiaViewSet, basename='estetica-dias')
router.register(r'estetica-turnos', ReservaEsteticaViewSet, basename='estetica-turnos')

urlpatterns = [
    path('disponibilidad/', get_disponibilidad, name='estetica-disponibilidad'),
    path('', include(router.urls)),
]
