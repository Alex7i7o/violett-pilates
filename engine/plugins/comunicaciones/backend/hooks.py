from backend_core.hooks import registry
from .whatsapp_service import notificar_cancelacion_clase, notificar_reserva_creada, notificar_cancelacion_usuario

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
        # TODO: Implement WhatsApp broadcast for available spot
        print(f"[WhatsApp] Alerta de cupo enviada para turno {turno.id}")
    return data

def on_reserva_recordatorio(data, **kwargs):
    reserva = data
    if reserva and reserva.turno:
        # TODO: Implement WhatsApp reminder for tomorrow's class
        print(f"[WhatsApp] Recordatorio enviado a {reserva.usuario.email} para turno {reserva.turno.id}")
    return data

registry.register('reserva_creada', on_reserva_creada)

registry.register('reserva_cancelada_a_tiempo', on_reserva_cancelada_a_tiempo)
registry.register('turno_cancelado_por_falta_cupo', on_turno_cancelado_por_falta_cupo)

registry.register('turno_alerta_cupo', on_turno_alerta_cupo)
registry.register('reserva_recordatorio', on_reserva_recordatorio)