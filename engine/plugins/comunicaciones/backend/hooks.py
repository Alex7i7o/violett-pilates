from backend_core.hooks import registry
from .whatsapp_service import WhatsAppClient, notificar_cancelacion_clase, notificar_reserva_creada, notificar_cancelacion_usuario
from .email_service import send_transactional_email
from django.conf import settings
import threading

def on_reserva_creada(data, **kwargs):
    reserva = data
    if reserva and reserva.turno:
        notificar_reserva_creada(reserva.usuario, reserva.turno)
        
        # Enviar email
        def send_email():
            try:
                context = {
                    'nombre': reserva.usuario.nombre,
                    'clase_nombre': reserva.turno.clase.nombre,
                    'fecha': reserva.turno.fecha.strftime('%d/%m/%Y'),
                    'hora': reserva.turno.hora_inicio.strftime('%H:%M'),
                    'profesor': reserva.turno.profesor.nombre if getattr(reserva.turno, 'profesor', None) else '-',
                    'app_url': getattr(settings, 'FRONTEND_URL', 'https://violett.com.ar/pilates/app')
                }
                send_transactional_email(
                    subject='¡Turno Confirmado!',
                    template_name='emails/booking_confirmation.html',
                    context=context,
                    recipient_list=[reserva.usuario.email]
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error sending email: {e}")
                
        threading.Thread(target=send_email, daemon=True).start()
    return data

def on_reserva_cancelada_a_tiempo(data, **kwargs):
    reserva = data
    if reserva and reserva.turno:
        notificar_cancelacion_usuario(reserva.usuario, reserva.turno)
        
        # Enviar email
        def send_email():
            try:
                context = {
                    'nombre': reserva.usuario.nombre,
                    'clase_nombre': reserva.turno.clase.nombre,
                    'fecha': reserva.turno.fecha.strftime('%d/%m/%Y'),
                    'hora': reserva.turno.hora_inicio.strftime('%H:%M'),
                    'app_url': getattr(settings, 'FRONTEND_URL', 'https://violett.com.ar/pilates/app')
                }
                send_transactional_email(
                    subject='Turno Cancelado',
                    template_name='emails/booking_cancellation.html',
                    context=context,
                    recipient_list=[reserva.usuario.email]
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error sending email: {e}")
                
        threading.Thread(target=send_email, daemon=True).start()
    return data

def on_turno_cancelado_por_falta_cupo(data, **kwargs):
    turno = data
    if turno:
        from core.models import Reserva
        reservas = Reserva.objects.filter(turno=turno)
        for r in reservas:
            notificar_cancelacion_clase(r.usuario, turno)
    return data

def on_turno_alerta_cupo(data, **kwargs):
    turno = data
    if turno:
        from core.models import Usuario
        usuarios = Usuario.objects.filter(rol='CLIENTE')
        client = WhatsAppClient()
        for u in usuarios:
            components = [{
                "type": "body",
                "parameters": [
                    {"type": "text", "text": u.nombre},
                    {"type": "text", "text": turno.clase.nombre},
                    {"type": "text", "text": f"{turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')}"}
                ]
            }]
            # Asumimos que vas a crear en Meta la plantilla "alerta_cupo_disponible"
            client._send_template(u.telefono or "1164142172", "alerta_cupo_disponible", components)
    return data

def on_reserva_recordatorio(data, **kwargs):
    reserva = data
    if reserva and reserva.turno:
        client = WhatsAppClient()
        components = [{
            "type": "body",
            "parameters": [
                {"type": "text", "text": reserva.usuario.nombre},
                {"type": "text", "text": reserva.turno.clase.nombre},
                {"type": "text", "text": reserva.turno.hora_inicio.strftime('%H:%M')}
            ]
        }]
        # Asumimos que vas a crear en Meta la plantilla "recordatorio_clase"
        client._send_template(reserva.usuario.telefono or "1164142172", "recordatorio_clase", components)
    return data

def on_plan_asignado(data, **kwargs):
    suscripcion = data.get('suscripcion')
    usuario = data.get('usuario')
    plan = data.get('plan')
    if suscripcion and usuario and plan:
        def send_email():
            try:
                context = {
                    'nombre': usuario.nombre,
                    'plan_nombre': plan.nombre,
                    'clases_restantes': suscripcion.clases_restantes,
                    'fecha_vencimiento': suscripcion.fecha_vencimiento.strftime('%d/%m/%Y'),
                    'app_url': getattr(settings, 'FRONTEND_URL', 'https://violett.com.ar/pilates/app')
                }
                send_transactional_email(
                    subject='¡Nuevo Plan Activo!',
                    template_name='emails/plan_assigned.html',
                    context=context,
                    recipient_list=[usuario.email]
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error sending email: {e}")
                
        threading.Thread(target=send_email, daemon=True).start()
    return data

registry.register('reserva_creada', on_reserva_creada)
registry.register('reserva_cancelada_a_tiempo', on_reserva_cancelada_a_tiempo)
registry.register('turno_cancelado_por_falta_cupo', on_turno_cancelado_por_falta_cupo)
registry.register('turno_alerta_cupo', on_turno_alerta_cupo)
registry.register('reserva_recordatorio', on_reserva_recordatorio)

registry.register('plan_asignado', on_plan_asignado)
