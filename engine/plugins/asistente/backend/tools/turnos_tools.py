import datetime
import logging
from typing import Optional, List, Dict
from django.utils import timezone
from django.db import transaction
from langchain_core.tools import tool

from core.models import Turno, Reserva, Usuario
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

@tool
def consultar_turnos_disponibles(fecha_str: str) -> str:
    """
    Consulta los turnos disponibles de Pilates Reformer para una fecha específica (formato YYYY-MM-DD o 'hoy', 'mañana').
    Retorna la lista de horarios con cupos libres (máximo 3 camillas por turno).
    """
    today = timezone.localdate()
    target_date = today

    if fecha_str.lower() == 'hoy':
        target_date = today
    elif fecha_str.lower() in ['mañana', 'manana']:
        target_date = today + datetime.timedelta(days=1)
    else:
        try:
            target_date = datetime.date.fromisoformat(fecha_str)
        except Exception:
            return f"No pude interpretar la fecha '{fecha_str}'. Por favor indicá una fecha en formato AAAA-MM-DD o 'hoy'/'mañana'."

    # Aseguramos generación desde plantillas si no existen
    try:
        from core.services import generar_turnos_desde_plantillas
        generar_turnos_desde_plantillas()
    except Exception as e:
        logger.warning(f"Error generando turnos: {e}")

    turnos = Turno.objects.filter(
        fecha=target_date,
        estado='PROGRAMADO',
        cupo_actual__gt=0
    ).select_related('clase', 'profesor').order_by('hora_inicio')

    if not turnos.exists():
        return f"No hay turnos con camillas disponibles para el {target_date.strftime('%d/%m/%Y')}."

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nombre = dias_semana[target_date.weekday()]

    resultado = [f"✦ Turnos disponibles para el {dia_nombre} {target_date.strftime('%d/%m')}:"]
    for t in turnos:
        profe = f" (Profe: {t.profesor.nombre})" if t.profesor and hasattr(t.profesor, 'nombre') else ""
        camillas_libres = t.cupo_actual
        resultado.append(f"• {t.hora_inicio.strftime('%H:%M')} hs - {t.clase.nombre}{profe} ({camillas_libres} camilla{'s' if camillas_libres > 1 else ''} libre{'s' if camillas_libres > 1 else ''}) [ID Turno: {t.id}]")

    return "\n".join(resultado)


@tool
def reservar_camilla_turno(usuario_id: str, turno_id: str) -> str:
    """
    Reserva 1 camilla de Reformer para una alumna en un turno específico.
    Valida atómicamente el cupo disponible (máximo 3 camillas) y descuenta 1 crédito de su plan activo.
    """
    if not usuario_id or not turno_id:
        return "Faltan datos de usuario o turno para confirmar la reserva."

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return "No se encontró el perfil de la alumna en el sistema."

    try:
        from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
    except ImportError:
        Suscripcion = None
        ReservaMembresia = None

    # Validar suscripción activa y créditos
    suscripcion = None
    if Suscripcion:
        suscripcion = Suscripcion.objects.filter(
            usuario=usuario,
            estado__in=['ACTIVO', 'AGOTADO'],
            fecha_vencimiento__gte=timezone.localdate()
        ).order_by('-fecha_inicio').first()

        if not suscripcion or suscripcion.clases_restantes <= 0:
            return "No tenés créditos disponibles en tu plan actual para agendar esta clase. ¿Querés que te pase las opciones para renovar tu abono?"

    # Transacción atómica con lock para prevenir sobreventa de la 3era camilla
    with transaction.atomic():
        try:
            turno = Turno.objects.select_for_update().get(id=turno_id)
        except Turno.DoesNotExist:
            return "El turno seleccionado ya no existe."

        if turno.cupo_actual <= 0:
            return f"Disculpá, justo se acaba de completar la última camilla libre de las {turno.hora_inicio.strftime('%H:%M')} hs."

        # Verificar si ya tiene reserva en este turno
        existing = Reserva.objects.filter(turno=turno, usuario=usuario).first()
        if existing:
            if existing.estado == 'CONFIRMADA':
                return f"Ya tenés una reserva confirmada para este turno de las {turno.hora_inicio.strftime('%H:%M')} hs."
            existing.estado = 'CONFIRMADA'
            existing.save()
            res = existing
        else:
            res = Reserva.objects.create(
                turno=turno,
                usuario=usuario,
                estado='CONFIRMADA'
            )

        # Descontar cupo
        turno.cupo_actual -= 1
        turno.save()

        # Descontar crédito
        if suscripcion and ReservaMembresia:
            ReservaMembresia.objects.get_or_create(reserva=res, defaults={'suscripcion': suscripcion})
            suscripcion.clases_restantes -= 1
            if suscripcion.clases_restantes == 0:
                suscripcion.estado = 'AGOTADO'
            suscripcion.save()

        # Disparar hooks
        from backend_core.hooks import registry
        registry.execute('reserva_creada', res)

    creditos_rest = f" Te quedan {suscripcion.clases_restantes} clases disponibles." if suscripcion else ""
    return f"✦ ¡Listo! Quedó confirmada tu camilla para el {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs en {turno.clase.nombre}.{creditos_rest}"


@tool
def consultar_mis_reservas_alumna(usuario_id: str) -> str:
    """
    Retorna la lista de reservas confirmadas futuras que tiene una alumna.
    """
    if not usuario_id:
        return "No estás identificada aún en el sistema."

    today = timezone.localdate()
    reservas = Reserva.objects.filter(
        usuario_id=usuario_id,
        estado='CONFIRMADA',
        turno__fecha__gte=today
    ).select_related('turno', 'turno__clase').order_by('turno__fecha', 'turno__hora_inicio')

    if not reservas.exists():
        return "Actualmente no tenés ninguna clase agendada a futuro."

    resultado = ["✦ Tus próximas clases agendadas:"]
    for r in reservas:
        t = r.turno
        tipo = " (Horario fijo)" if r.es_recurrente else " (Puntual)"
        resultado.append(f"• {t.fecha.strftime('%d/%m')} a las {t.hora_inicio.strftime('%H:%M')} hs - {t.clase.nombre}{tipo} [Reserva ID: {r.id}]")

    return "\n".join(resultado)
