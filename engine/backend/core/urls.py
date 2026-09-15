from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_auth import ThrottledLoginView
from .views import (
    TurnosDisponiblesView, BookTurnoView, CancelTurnoView, ClientProfileView, GoogleLogin, ClientHistoryView
)
from .admin_views import (
    AdminAgendaView,
    DashboardStatsView,
    AdminTurnoViewSet,
    AdminReservaViewSet,
    ClaseViewSet,
    PlantillaTurnoViewSet,
    AdminUsuarioViewSet,
    ConfiguracionView,
)

router = DefaultRouter()
# Admin routes
router.register(r'admin/alumnos', AdminUsuarioViewSet, basename='admin-alumnos')
router.register(r'admin/clases', ClaseViewSet, basename='admin-clase')
router.register(r'admin/plantillas', PlantillaTurnoViewSet, basename='admin-plantilla')
router.register(r'admin/turnos', AdminTurnoViewSet, basename='admin-turno')
router.register(r'admin/reservas', AdminReservaViewSet, basename='admin-reserva')

urlpatterns = [
    path('admin/agenda/', AdminAgendaView.as_view(), name='admin-agenda'),
    path('', include(router.urls)),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/login/', ThrottledLoginView.as_view(), name='throttled_login'),
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    
    path('profile/', ClientProfileView.as_view(), name='client_profile'),
    path('turnos/', TurnosDisponiblesView.as_view(), name='turnos_disponibles'),
    path('reservas/book/', BookTurnoView.as_view(), name='book_turno'),
    path('reservas/cancel/', CancelTurnoView.as_view(), name='cancel_turno'),
    path('reservas/historial/', ClientHistoryView.as_view(), name='client_history'),
    path('admin/dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('admin/config/', ConfiguracionView.as_view(), name='admin-config'),
]
