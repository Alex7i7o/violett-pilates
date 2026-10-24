from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, SuscripcionViewSet, AsignarPlanView, ReactivarPlanView, CancelarPlanView, CancelarClasesFuturasView

router = DefaultRouter()
router.register(r'admin/planes', PlanViewSet, basename='admin-planes')
router.register(r'planes', PlanViewSet, basename='planes')
router.register(r'admin/suscripciones', SuscripcionViewSet, basename='admin-suscripciones')

urlpatterns = [
    path('admin/alumnos/<str:usuario_id>/asignar-plan/', AsignarPlanView.as_view(), name='asignar-plan'),
    path('admin/alumnos/<str:usuario_id>/reactivar-plan/', ReactivarPlanView.as_view(), name='reactivar-plan'),
    path('admin/alumnos/<str:usuario_id>/cancelar-plan/', CancelarPlanView.as_view(), name='cancelar-plan'),
    path('admin/alumnos/<str:usuario_id>/cancelar-clases-futuras/', CancelarClasesFuturasView.as_view(), name='cancelar-clases-futuras'),
    path('', include(router.urls)),
]
