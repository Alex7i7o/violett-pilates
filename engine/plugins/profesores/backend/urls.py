from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfesorViewSet, ProfesorDashboardView, AssignPlantillaView, AssignTurnoView

router = DefaultRouter()
router.register(r'admin/profesores', ProfesorViewSet, basename='admin-profesores')
router.register(r'profesores', ProfesorViewSet, basename='profesores')

urlpatterns = [
    path('profesor/dashboard/', ProfesorDashboardView.as_view(), name='profesor-dashboard'),
    path('profesor/plantillas/<uuid:pk>/assign/', AssignPlantillaView.as_view(), name='assign-plantilla'),
    path('profesor/turnos/<uuid:pk>/assign/', AssignTurnoView.as_view(), name='assign-turno'),
    path('', include(router.urls)),
]