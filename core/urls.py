# Developed by FireSeed - Fueling Innovation
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientHistoryView, TurnosDisponiblesView, BookTurnoView, CancelTurnoView, ClientProfileView, CancelRecurrenciaView, GoogleLogin, CrearResenaView
from .views_webhooks import MercadoPagoWebhookView
from .admin_views import (
    ProfesorViewSet, AdminTurnoViewSet, AdminAlumnoViewSet, 
    AdminAgendaView, AdminReservaAsistenciaView,
    PlanViewSet, PlantillaTurnoViewSet, ClaseViewSet
)
from .profesor_views import ProfesorDashboardView, AssignClaseView, AssignPlantillaView, ProfesorAsistenciaView

router = DefaultRouter()
router.register(r'admin/profesores', ProfesorViewSet, basename='admin-profesores')
router.register(r'admin/turnos', AdminTurnoViewSet, basename='admin-turnos')
router.register(r'admin/alumnos', AdminAlumnoViewSet, basename='admin-alumnos')
router.register(r'admin/planes', PlanViewSet, basename='admin-planes')
router.register(r'admin/plantillas', PlantillaTurnoViewSet, basename='admin-plantillas')
router.register(r'admin/clases', ClaseViewSet, basename='admin-clases')

urlpatterns = [
    path('webhooks/mercadopago/', MercadoPagoWebhookView.as_view(), name='webhook_mp'),

    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    
    path('profile/', ClientProfileView.as_view(), name='client_profile'),
    path('turnos/', TurnosDisponiblesView.as_view(), name='turnos_disponibles'),
    path('reservas/book/', BookTurnoView.as_view(), name='book_turno'),
    path('reservas/cancel/', CancelTurnoView.as_view(), name='cancel_turno'),
    path('recurrencias/cancel/', CancelRecurrenciaView.as_view(), name='cancel_recurrencia'),
    
    path('admin/agenda/', AdminAgendaView.as_view(), name='admin_agenda'),
    path('admin/reservas/<uuid:pk>/asistencia/', AdminReservaAsistenciaView.as_view(), name='admin_asistencia'),
    path('admin/alumnos/<uuid:pk>/asignar-plan/', AdminAlumnoViewSet.as_view({'post': 'asignar_plan'}), name='asignar_plan'),
    
    path('profesor/dashboard/', ProfesorDashboardView.as_view(), name='profesor_dashboard'),
    path('profesor/reservas/<uuid:reserva_id>/asistencia/', ProfesorAsistenciaView.as_view(), name='profesor-asistencia'),
    path('profesor/turnos/<uuid:turno_id>/assign/', AssignClaseView.as_view(), name='profesor_assign'),
    path('profesor/plantillas/<uuid:plantilla_id>/assign/', AssignPlantillaView.as_view(), name='profesor_plantilla_assign'),
    path('resenas/', CrearResenaView.as_view(), name='crear-resena'),
] + router.urls
