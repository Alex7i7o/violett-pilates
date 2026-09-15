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

registry.register('reserva_creada', on_reserva_creada)
registry.register('reserva_cancelada_a_tiempo', on_reserva_cancelada_a_tiempo)
registry.register('turno_cancelado_por_falta_cupo', on_turno_cancelado_por_falta_cupo)
