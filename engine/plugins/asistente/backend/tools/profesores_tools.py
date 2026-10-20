import datetime
import logging
from django.utils import timezone
from langchain_core.tools import tool

from core.models import Turno, Usuario
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

@tool
def consultar_mis_clases_profesor(profesor_usuario_id: str) -> str:
    """
    Retorna la lista de clases asignadas a una profesora o profesor para los próximos 7 días.
    """
    if not profesor_usuario_id:
        return "No estás identificada como profesora en el sistema."

    today = timezone.localdate()
    next_week = today + datetime.timedelta(days=7)

    turnos = Turno.objects.filter(
        profesor_id=profesor_usuario_id,
        fecha__gte=today,
        fecha__lte=next_week,
        estado='PROGRAMADO'
    ).select_related('clase').order_by('fecha', 'hora_inicio')

    if not turnos.exists():
        return "No tenés clases asignadas programadas para los próximos 7 días."

    resultado = ["✦ Tus clases asignadas para los próximos días:"]
    for t in turnos:
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        dia_nom = dias[t.fecha.weekday()]
        resultado.append(f"• {dia_nom} {t.fecha.strftime('%d/%m')} {t.hora_inicio.strftime('%H:%M')} hs - {t.clase.nombre} ({t.cupo_actual}/3 camillas libres) [ID Turno: {t.id}]")

    return "\n".join(resultado)


@tool
def gestionar_ausencia_y_buscar_reemplazo(profesor_usuario_id: str, turno_id: str, motivo: str = "") -> str:
    """
    Permite a una profesora avisar que no puede dar una clase.
    El sistema busca automáticamente a otras profesoras activas del staff que no tengan clase asignada en ese horario
    y les envía una solicitud de guardia/reemplazo por WhatsApp.
    """
    if not profesor_usuario_id or not turno_id:
        return "Se necesita el ID de la profesora y el ID del turno a cubrir."

    try:
        turno = Turno.objects.select_related('clase', 'profesor').get(id=turno_id)
    except Turno.DoesNotExist:
        return "El turno especificado no existe."

    profe_titular = turno.profesor
    nombre_titular = f"{profe_titular.nombre} {profe_titular.apellido}".strip() if profe_titular else "Una profesora"

    # Buscar otras profesoras activas
    # En Violett, las profesoras son Usuario con is_profesor=True o rol='profesor'
    otros_profes = Usuario.objects.filter(
        is_active=True
    ).exclude(id=profesor_usuario_id)

    # Filtrar por rol profesor si existe el campo
    if hasattr(Usuario, 'rol'):
        otros_profes = otros_profes.filter(rol='profesor')
    elif hasattr(Usuario, 'is_profesor'):
        otros_profes = otros_profes.filter(is_profesor=True)

    # Identificar quiénes no tienen clase a esa misma hora
    candidatas = []
    for p in otros_profes:
        tiene_clase = Turno.objects.filter(
            profesor=p,
            fecha=turno.fecha,
            hora_inicio=turno.hora_inicio,
            estado='PROGRAMADO'
        ).exists()
        if not tiene_clase and p.telefono:
            candidatas.append(p)

    if not candidatas:
        # Avisar a la dueña que no hay suplentes automáticos
        config = get_asistente_config()
        tel_duena = config.get('telefono_duena')
        if tel_duena:
            client = WhatsAppClient()
            client.send_text_message(
                tel_duena,
                f"⚠️ AVISO URGENTE: {nombre_titular} no puede dar la clase de {turno.clase.nombre} del {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs (Motivo: {motivo or 'No especificado'}). No se encontraron profesoras disponibles en el staff."
            )
        return f"Entendido, registré tu aviso de ausencia. No encontré profesoras con disponibilidad libre para ese bloque, así que ya le notifiqué con urgencia a la dirección del estudio para coordinar la cobertura."

    # Enviar WhatsApp a las candidatas
    client = WhatsAppClient()
    contactadas = []
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias[turno.fecha.weekday()]

    for p in candidatas:
        clean_phone = p.telefono.replace('+', '').replace(' ', '')
        nombre_p = p.nombre or "profe"
        msg = (
            f"¡Hola {nombre_p}! ✦ {nombre_titular} no va a poder dar la clase de {turno.clase.nombre} "
            f"del {dia_nom} {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs. "
            f"¿Tendrías disponibilidad para cubrirla? Si podés, respondé 'Sí puedo cubrir' y te la asigno."
        )
        client.send_text_message(clean_phone, msg)
        contactadas.append(f"{p.nombre} ({p.telefono})")

    # Guardar en metadata de auditoría
    from ..models import RegistroAccionIA
    RegistroAccionIA.objects.create(
        tipo_accion='TURNO_REASIGNADO',
        descripcion=f"Búsqueda de reemplazo iniciada para clase {turno.clase.nombre} ({turno.fecha} {turno.hora_inicio}). Contactadas: {len(contactadas)} profesoras.",
        payload={'turno_id': str(turno.id), 'contactadas': contactadas, 'motivo': motivo}
    )

    return f"✦ Listo, no te preocupes. Ya le envié un mensaje a {len(contactadas)} profesoras del staff que están libres en ese horario para coordinar la suplencia. Apenas alguna confirme, queda reasignada y te avisamos."
