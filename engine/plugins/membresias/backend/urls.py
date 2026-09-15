from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, SuscripcionViewSet, AsignarPlanView

router = DefaultRouter()
router.register(r'admin/planes', PlanViewSet, basename='admin-planes')
router.register(r'planes', PlanViewSet, basename='planes')
router.register(r'admin/suscripciones', SuscripcionViewSet, basename='admin-suscripciones')

urlpatterns = [
    path('admin/alumnos/<str:usuario_id>/asignar-plan/', AsignarPlanView.as_view(), name='asignar-plan'),
    path('', include(router.urls)),
]
