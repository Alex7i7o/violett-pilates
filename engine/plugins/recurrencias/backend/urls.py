from django.urls import path
from .views import CancelRecurrenciaView, AdminRecurrenciaView

urlpatterns = [
    path('recurrencias/cancel/', CancelRecurrenciaView.as_view(), name='cancel_recurrencia'),
    path('admin/alumnos/<str:usuario_id>/recurrencias/', AdminRecurrenciaView.as_view(), name='admin_recurrencia'),
    path('admin/alumnos/<str:usuario_id>/recurrencias/<str:recurrencia_id>/', AdminRecurrenciaView.as_view(), name='admin_recurrencia_detail'),
]