from django.urls import path
from .views import (
    ConversacionesAdminView,
    ConversacionMensajesAdminView,
    TogglePausaHumanoView,
    EnviarMensajeManualAdminView,
    AsistenteConfigView
)

urlpatterns = [
    path('admin/asistente/conversaciones/', ConversacionesAdminView.as_view(), name='asistente-conversaciones'),
    path('admin/asistente/conversaciones/<str:conversacion_id>/mensajes/', ConversacionMensajesAdminView.as_view(), name='asistente-mensajes'),
    path('admin/asistente/conversaciones/<str:conversacion_id>/pausar/', TogglePausaHumanoView.as_view(), name='asistente-pausar'),
    path('admin/asistente/conversaciones/<str:conversacion_id>/enviar/', EnviarMensajeManualAdminView.as_view(), name='asistente-enviar-mensaje'),
    path('admin/asistente/config/', AsistenteConfigView.as_view(), name='asistente-config'),
]
