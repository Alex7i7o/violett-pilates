from backend_core.hooks import registry
from .whatsapp_service import WhatsAppClient, notificar_cancelacion_clase, notificar_reserva_creada, notificar_cancelacion_usuario

def on_reserva_creada(data, **kwargs):
    reserva = data
    if reserva and reserva.turno:
        notificar_reserva_creada(reserva.usuario, reserva.turno)
    return data

def on_reserva_cancelada_a_tiempo(data, **kwargs):
    reserva = data
    if reserva and reserva.turno:
        notificar_cancelacion_usuario(reserva.usuario, reserva.turno)
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

registry.register('reserva_creada', on_reserva_creada)
registry.register('reserva_cancelada_a_tiempo', on_reserva_cancelada_a_tiempo)
registry.register('turno_cancelado_por_falta_cupo', on_turno_cancelado_por_falta_cupo)
registry.register('turno_alerta_cupo', on_turno_alerta_cupo)
registry.register('reserva_recordatorio', on_reserva_recordatorio)
