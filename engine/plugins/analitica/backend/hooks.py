from backend_core.hooks import registry
from .models import MetricaInteractiva, RegistroFacturacion

def on_plan_asignado(data, **kwargs):
    suscripcion = data.get('suscripcion')
    if suscripcion:
        RegistroFacturacion.objects.create(
            usuario=suscripcion.usuario,
            plan_nombre=suscripcion.plan.nombre,
            monto=suscripcion.plan.precio,
            suscripcion_id=str(suscripcion.id)
        )
    return data

def on_reserva_creada(reserva, **kwargs):
    if reserva.usuario and reserva.usuario.rol == 'CLIENTE':
        MetricaInteractiva.objects.create(tipo='AUTO_RESERVA', usuario=reserva.usuario)
    return reserva

def on_reserva_cancelada(reserva, **kwargs):
    if reserva.usuario and reserva.usuario.rol == 'CLIENTE':
        MetricaInteractiva.objects.create(tipo='AUTO_CANCEL', usuario=reserva.usuario)
    return reserva

def on_email_enviado(data, **kwargs):
    MetricaInteractiva.objects.create(tipo='EMAIL')
    return data

def on_wpp_enviado(data, **kwargs):
    MetricaInteractiva.objects.create(tipo='WPP')
    return data

registry.register('plan_asignado', on_plan_asignado)
registry.register('reserva_creada', on_reserva_creada)
registry.register('reserva_cancelada_a_tiempo', on_reserva_cancelada)
registry.register('reserva_cancelada_tardia', on_reserva_cancelada)
registry.register('email_enviado_tracker', on_email_enviado)
registry.register('wpp_enviado_tracker', on_wpp_enviado)
