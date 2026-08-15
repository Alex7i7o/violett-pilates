# Developed by FireSeed - Fueling Innovation
from django.urls import path
from .views import ClientProfileView, TurnosDisponiblesView, BookTurnoView, CancelTurnoView, CancelRecurrenciaView

urlpatterns = [
    path('profile/', ClientProfileView.as_view(), name='client_profile'),
    path('turnos/', TurnosDisponiblesView.as_view(), name='turnos_disponibles'),
    path('reservas/book/', BookTurnoView.as_view(), name='book_turno'),
    path('reservas/cancel/', CancelTurnoView.as_view(), name='cancel_turno'),
    path('recurrencias/cancel/', CancelRecurrenciaView.as_view(), name='cancel_recurrencia'),
]
