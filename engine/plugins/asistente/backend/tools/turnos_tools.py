import datetime
import logging
from typing import Optional, List, Dict
from django.utils import timezone
from django.db import transaction
from langchain_core.tools import tool

from core.models import Turno, Reserva, Usuario
from ..config_loader import get_asistente_config
from .profesores_tools import resolver_fecha, resolver_hora, obtener_profesor_de_turno

logger = logging.getLogger(__name__)

@tool
def consultar_turnos_disponibles(fecha_str: str) -> str:
    """
    Consulta los turnos disponibles de Pilates Reformer para una fecha específica ('hoy', 'mañana', 'lunes', '2026-10-23', etc.).
    Retorna la lista de horarios con cupos libres (máximo 3 camillas por turno).
    NUNCA expongas IDs numéricos al usuario final.
    """
    target_date = resolver_fecha(fecha_str)

    # Aseguramos generación desde plantillas únicamente si aún no hay turnos generados para esa fecha
    if not Turno.objects.filter(fecha=target_date).exists():
        try:
            from core.services import generar_turnos_desde_plantillas
            generar_turnos_desde_plantillas()
        except Exception as e:
            logger.warning(f"Error generando turnos: {e}")

    turnos = Turno.objects.filter(
        fecha=target_date,
        estado='PROGRAMADO',
        cupo_actual__gt=0
    ).select_related('clase').order_by('hora_inicio')

    if not turnos.exists():
        return f"No hay turnos con camillas disponibles para el {target_date.strftime('%d/%m/%Y')}."

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nombre = dias_semana[target_date.weekday()]

    resultado = [f"✦ Turnos disponibles para el {dia_nombre} {target_date.strftime('%d/%m')}:"]
    for t in turnos:
        prof_obj = obtener_profesor_de_turno(t)
        profe = f" (Profe: {prof_obj.nombre})" if prof_obj and hasattr(prof_obj, 'nombre') else ""
        camillas_libres = t.cupo_actual
        resultado.append(
            f"• {t.hora_inicio.strftime('%H:%M')} hs - {t.clase.nombre}{profe} "
            f"({camillas_libres} camilla{'s' if camillas_libres > 1 else ''} libre{'s' if camillas_libres > 1 else ''})"
        )

    return "\n".join(resultado)


@tool
def reservar_camilla_turno(usuario_id: str, fecha_o_dia: str = "", hora_str: str = "", turno_id: str = "") -> str:
    """
    Reserva 1 camilla de Reformer para una alumna.
    Podés especificar 'turno_id' O 'fecha_o_dia' (ej: 'hoy', 'mañana', 'viernes') junto a 'hora_str' (ej: '18:00').
    Valida atómicamente el cupo disponible (máximo 3 camillas) y descuenta 1 crédito de su plan activo.
    """
    if not usuario_id:
        return "No estás identificada aún en el sistema para realizar la reserva."

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

    # Buscar turno
    turno = None
    if turno_id:
        try:
            turno = Turno.objects.filter(id=turno_id).first()
        except Exception:
            turno = None

    if not turno and fecha_o_dia:
        target_date = resolver_fecha(fecha_o_dia)
        target_time = resolver_hora(hora_str) if hora_str else None
        qs = Turno.objects.filter(fecha=target_date, estado='PROGRAMADO')
        if target_time:
            qs = qs.filter(hora_inicio__hour=target_time.hour, hora_inicio__minute=target_time.minute)
        turno = qs.first()

    if not turno:
        return f"No se encontró ningún turno programado para {fecha_o_dia} a las {hora_str} hs."

    # Transacción atómica con lock para prevenir sobreventa de la 3era camilla
    with transaction.atomic():
        t_locked = Turno.objects.select_for_update().get(id=turno.id)

        if t_locked.cupo_actual <= 0:
            return f"Disculpá, justo se acaba de completar la última camilla libre de las {t_locked.hora_inicio.strftime('%H:%M')} hs."

        # Verificar si ya tiene reserva en este turno
        existing = Reserva.objects.filter(turno=t_locked, usuario=usuario).first()
        if existing:
            if existing.estado == 'CONFIRMADA':
                return f"Ya tenés una reserva confirmada para este turno de las {t_locked.hora_inicio.strftime('%H:%M')} hs."
            existing.estado = 'CONFIRMADA'
            existing.save()
            res = existing
        else:
            res = Reserva.objects.create(
                turno=t_locked,
                usuario=usuario,
                estado='CONFIRMADA'
            )

        # Descontar cupo
        t_locked.cupo_actual -= 1
        t_locked.save()

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
    return f"✦ ¡Listo! Quedó confirmada tu camilla para el {t_locked.fecha.strftime('%d/%m')} a las {t_locked.hora_inicio.strftime('%H:%M')} hs en {t_locked.clase.nombre}.{creditos_rest}"


@tool
def consultar_mis_reservas_alumna(usuario_id: str) -> str:
    """
    Retorna la lista de reservas confirmadas futuras que tiene una alumna.
    Muestra los turnos prolijamente ordenados por fecha y hora, sin IDs internos.
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

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    resultado = ["✦ Tus próximas clases agendadas:"]
    for r in reservas:
        t = r.turno
        dia_nombre = dias_semana[t.fecha.weekday()]
        tipo = " (Horario fijo semanal)" if getattr(r, 'es_recurrente', False) else " (Clase puntual)"
        resultado.append(f"• {dia_nombre} {t.fecha.strftime('%d/%m')} a las {t.hora_inicio.strftime('%H:%M')} hs - {t.clase.nombre}{tipo}")

    return "\n".join(resultado)


@tool
def cancelar_reserva_alumna(usuario_id: str, fecha_o_dia: str, hora_str: str = "") -> str:
    """
    Cancela una reserva de clase de una alumna, aplicando la regla de negocio estricta de 24 horas:
    - Con MÁS de 24 hs de anticipación: Cancela la reserva, libera la camilla y RECUPERA el crédito a su abono.
    - Con MENOS de 24 hs de anticipación: Cancela la reserva y libera la camilla, pero la alumna PIERDE el crédito de la clase (política del estudio).
    Parámetros:
    - usuario_id: ID del usuario
    - fecha_o_dia: 'hoy', 'mañana', 'lunes', '2026-10-23'
    - hora_str: '18:00', '10:30', etc.
    """
    if not usuario_id:
        return "No estás identificada aún en el sistema."

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return "No se encontró el perfil de la alumna."

    target_date = resolver_fecha(fecha_o_dia)
    target_time = resolver_hora(hora_str) if hora_str else None

    qs = Reserva.objects.filter(
        usuario=usuario,
        estado='CONFIRMADA',
        turno__fecha=target_date
    ).select_related('turno', 'turno__clase')

    if target_time:
        qs = qs.filter(turno__hora_inicio__hour=target_time.hour, turno__hora_inicio__minute=target_time.minute)

    reserva = qs.first()
    if not reserva:
        hora_txt = f" a las {hora_str} hs" if hora_str else ""
        return f"No tenés ninguna reserva confirmada para el {target_date.strftime('%d/%m')}{hora_txt}."

    turno = reserva.turno

    # Cálculo exacto de horas de anticipación
    ahora = timezone.localtime()
    tz = ahora.tzinfo
    clase_dt = datetime.datetime.combine(turno.fecha, turno.hora_inicio)
    if timezone.is_naive(clase_dt):
        clase_dt = timezone.make_aware(clase_dt, tz)

    horas_anticipacion = (clase_dt - ahora).total_seconds() / 3600.0

    # Buscar suscripción vinculada
    try:
        from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
        res_mem = ReservaMembresia.objects.filter(reserva=reserva).first()
        suscripcion = res_mem.suscripcion if res_mem else None
        if not suscripcion:
            suscripcion = Suscripcion.objects.filter(
                usuario=usuario,
                estado__in=['ACTIVO', 'AGOTADO']
            ).order_by('-fecha_inicio').first()
    except ImportError:
        suscripcion = None

    with transaction.atomic():
        t_locked = Turno.objects.select_for_update().get(id=turno.id)
        reserva.estado = 'CANCELADA'
        reserva.save()

        # Liberar cupo de camilla
        t_locked.cupo_actual += 1
        t_locked.save()

        # Aplicar regla de 24 horas
        if horas_anticipacion >= 24.0:
            if suscripcion:
                suscripcion.clases_restantes += 1
                if suscripcion.estado == 'AGOTADO':
                    suscripcion.estado = 'ACTIVO'
                suscripcion.save()
            recupero_credito = True
        else:
            recupero_credito = False

        from backend_core.hooks import registry
        registry.execute('reserva_cancelada', reserva)

    if recupero_credito:
        creditos_rest = f" Tu saldo actual es de {suscripcion.clases_restantes} clases disponibles." if suscripcion else ""
        return (
            f"✦ Tu clase del {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs ha sido cancelada con éxito. "
            f"Como cancelaste con más de 24 hs de anticipación, recuperaste tu crédito para volver a agendar en cualquier momento del mes.{creditos_rest}"
        )
    else:
        return (
            f"✦ Tu clase del {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs ha sido cancelada y la camilla quedó liberada. "
            f"Tené en cuenta que, según la política oficial del estudio (cancelación con menos de 24 hs de anticipación), "
            f"el crédito de la clase no se recupera ✦."
        )
