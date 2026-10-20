import datetime
import logging
from django.utils import timezone
from core.models import Turno, Reserva
from .models import Recurrencia
from backend_core.hooks import registry

logger = logging.getLogger(__name__)

def auto_agendar_recurrencias_usuario(usuario, suscripcion):
    """
    Agenda automáticamente los turnos fijos (recurrencias activas) de un usuario
    utilizando los créditos disponibles en su suscripción hasta la fecha de vencimiento.
    Retorna la cantidad de reservas creadas.
    """
    if not suscripcion or suscripcion.clases_restantes <= 0:
        return 0

    recs = Recurrencia.objects.filter(usuario=usuario, is_active=True).select_related('clase')
    if not recs.exists():
        return 0

    # Nos aseguramos de que existan los turnos generados desde plantillas para los próximos 30 días
    try:
        from core.services import generar_turnos_desde_plantillas
        generar_turnos_desde_plantillas()
    except Exception as e:
        logger.warning(f"Error generando turnos desde plantillas: {e}")

    try:
        from plugins.membresias.backend.models import ReservaMembresia
    except ImportError:
        ReservaMembresia = None

    today = timezone.localdate()
    slots = [(r.clase_id, r.dia_semana, r.hora_inicio) for r in recs]

    future_turnos = Turno.objects.filter(
        fecha__gte=today,
        fecha__lte=suscripcion.fecha_vencimiento,
        estado='PROGRAMADO',
        cupo_actual__gt=0
    ).select_related('clase').order_by('fecha', 'hora_inicio')

    reservas_creadas = 0

    for t in future_turnos:
        if suscripcion.clases_restantes <= 0:
            break

        # Verificar si este turno coincide con alguna de las recurrencias del usuario
        matches = any(
            t.clase_id == c_id and t.fecha.isoweekday() == dia and t.hora_inicio == hora
            for c_id, dia, hora in slots
        )

        if not matches:
            continue

        existing_reserva = Reserva.objects.filter(turno=t, usuario=usuario).first()
        if existing_reserva:
            if existing_reserva.estado == 'CONFIRMADA':
                continue
            existing_reserva.es_recurrente = True
            existing_reserva.estado = 'CONFIRMADA'
            existing_reserva.save()
            if ReservaMembresia:
                ReservaMembresia.objects.get_or_create(reserva=existing_reserva, defaults={'suscripcion': suscripcion})
            registry.execute('reserva_creada', existing_reserva)
        else:
            res = Reserva.objects.create(
                turno=t,
                usuario=usuario,
                es_recurrente=True,
                estado='CONFIRMADA'
            )
            if ReservaMembresia:
                ReservaMembresia.objects.create(reserva=res, suscripcion=suscripcion)
            registry.execute('reserva_creada', res)

        t.cupo_actual -= 1
        t.save()
        suscripcion.clases_restantes -= 1
        reservas_creadas += 1

    if suscripcion.clases_restantes <= 0:
        suscripcion.estado = 'AGOTADO'
    suscripcion.save()

    logger.info(f"Auto-agendadas {reservas_creadas} clases fijas para {usuario.email}. Créditos restantes: {suscripcion.clases_restantes}")
    return reservas_creadas
