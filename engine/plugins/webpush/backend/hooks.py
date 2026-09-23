from backend_core.hooks import registry
from .services import send_webpush
import logging

logger = logging.getLogger(__name__)

def on_reserva_creada(data, **kwargs):
    reserva = data
    if reserva and reserva.turno:
        usuario = reserva.usuario
        turno = reserva.turno
        clase = turno.clase
        title = "Reserva Confirmada"
        body = f"Has reservado exitosamente la clase de {clase.nombre} el {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')}."
        send_webpush(usuario, title, body, data={'url': '/perfil'})
    return data

def on_reserva_cancelada_a_tiempo(data, **kwargs):
    reserva = data
    if reserva and reserva.turno:
        usuario = reserva.usuario
        turno = reserva.turno
        clase = turno.clase
        title = "Reserva Cancelada"
        body = f"Has cancelado la clase de {clase.nombre} del {turno.fecha.strftime('%d/%m')}."
        send_webpush(usuario, title, body, data={'url': '/perfil'})
    return data

def on_turno_cancelado_por_falta_cupo(data, **kwargs):
    turno = data
    if turno:
        from core.models import Reserva
        reservas = Reserva.objects.filter(turno=turno)
        clase = turno.clase
        for r in reservas:
            title = "Clase Cancelada"
            body = f"Lo sentimos, la clase de {clase.nombre} del {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} fue cancelada por no llegar al cupo mínimo."
            send_webpush(r.usuario, title, body, data={'url': '/perfil'})
    return data


def on_turno_alerta_cupo(data, **kwargs):
    turno = data
    if turno:
        from core.models import Usuario
        usuarios = Usuario.objects.filter(rol='CLIENTE')
        clase = turno.clase
        title = "¡Cupo disponible!"
        body = f"Queda 1 lugar libre para la clase de {clase.nombre} del {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')}."
        for u in usuarios:
            send_webpush(u, title, body, data={'url': '/'})
    return data

def on_reserva_recordatorio(data, **kwargs):
    reserva = data
    if reserva and reserva.turno:
        usuario = reserva.usuario
        turno = reserva.turno
        clase = turno.clase
        title = "Recordatorio de Clase"
        body = f"Te esperamos mañana para la clase de {clase.nombre} a las {turno.hora_inicio.strftime('%H:%M')} hs."
        send_webpush(usuario, title, body, data={'url': '/mis-reservas'})
    return data

registry.register('reserva_creada', on_reserva_creada)

registry.register('reserva_cancelada_a_tiempo', on_reserva_cancelada_a_tiempo)
registry.register('turno_cancelado_por_falta_cupo', on_turno_cancelado_por_falta_cupo)

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from core.models import Turno, PlantillaTurno, Usuario

@receiver(post_save, sender=Turno)
def notify_bolsa_turno(sender, instance, created, **kwargs):
    if not created: return
    try:
        instance.profesor_asignado
    except ObjectDoesNotExist:
        profesores = Usuario.objects.filter(rol='PROFESOR')
        for profe in profesores:
            send_webpush(
                profe, 
                "Nuevo horario en Bolsa", 
                f"Una clase de {instance.clase.nombre} necesita profesor para el {instance.fecha.strftime('%d/%m')}", 
                data={'url': '/profesor/dashboard#bolsa'}
            )

@receiver(post_save, sender=PlantillaTurno)
def notify_bolsa_plantilla(sender, instance, created, **kwargs):
    if not created: return
    try:
        instance.profesor_asignado
    except ObjectDoesNotExist:
        profesores = Usuario.objects.filter(rol='PROFESOR')
        for profe in profesores:
            send_webpush(
                profe, 
                "Nuevo Horario Fijo en Bolsa", 
                f"Se liberó un horario fijo de {instance.clase.nombre} los días {['', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][instance.dia_semana]}", 
                data={'url': '/profesor/dashboard#bolsa'}
            )


registry.register('turno_alerta_cupo', on_turno_alerta_cupo)
registry.register('reserva_recordatorio', on_reserva_recordatorio)