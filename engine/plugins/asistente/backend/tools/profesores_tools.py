import re
import datetime
import logging
from django.utils import timezone
from django.db.models import Q
from langchain_core.tools import tool

from core.models import Turno, Usuario
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

def resolver_fecha(fecha_str: str) -> datetime.date:
    """Interpreta fechas naturales en español: 'hoy', 'mañana', 'martes', 'jueves', '24/10', '2026-10-24'."""
    today = timezone.localdate()
    s = fecha_str.strip().lower()
    if s in ['hoy', 'today']:
        return today
    if s in ['mañana', 'manana', 'tomorrow']:
        return today + datetime.timedelta(days=1)
    if s in ['pasado mañana', 'pasado manana']:
        return today + datetime.timedelta(days=2)

    dias_semana = {
        'lunes': 0, 'lun': 0,
        'martes': 1, 'mar': 1,
        'miercoles': 2, 'miércoles': 2, 'mie': 2, 'mié': 2,
        'jueves': 3, 'jue': 3,
        'viernes': 4, 'vie': 4,
        'sabado': 5, 'sábado': 5, 'sab': 5, 'sáb': 5,
        'domingo': 6, 'dom': 6,
    }
    for dia_nombre, dia_idx in dias_semana.items():
        if dia_nombre in s:
            dias_adelante = (dia_idx - today.weekday()) % 7
            if dias_adelante == 0 and ('proximo' in s or 'próximo' in s):
                dias_adelante = 7
            return today + datetime.timedelta(days=dias_adelante)

    m = re.search(r'(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?', s)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        if year < 100:
            year += 2000
        return datetime.date(year, month, day)

    try:
        return datetime.date.fromisoformat(s)
    except Exception:
        return today


def resolver_hora(hora_str: str) -> datetime.time:
    """Interpreta cadenas horarias como '18', '18:00', '18hs', '10:30', '6pm'."""
    s = hora_str.strip().lower()
    m = re.search(r'(\d{1,2})(?::(\d{2}))?', s)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        if 'pm' in s and hour < 12:
            hour += 12
        return datetime.time(hour, minute)
    return datetime.time(9, 0)


def obtener_profesor_de_turno(turno: Turno):
    """
    Obtiene el objeto Profesor asignado al turno (directamente o por plantilla).
    """
    try:
        from plugins.profesores.backend.models import TurnoProfesor
        if hasattr(turno, 'profesor_asignado') and turno.profesor_asignado:
            return turno.profesor_asignado.profesor
        if turno.plantilla and hasattr(turno.plantilla, 'profesor_asignado') and turno.plantilla.profesor_asignado:
            return turno.plantilla.profesor_asignado.profesor
    except Exception:
        pass
    return None


def asignar_profesor_a_turno(turno: Turno, profesor_obj):
    """
    Asigna o reasigna un profesor a un turno a través del modelo TurnoProfesor.
    """
    from plugins.profesores.backend.models import TurnoProfesor
    tp, _ = TurnoProfesor.objects.update_or_create(
        turno=turno,
        defaults={'profesor': profesor_obj}
    )
    return tp


def buscar_profesor(nombre_o_id: str):
    """
    Busca una profesora activa en el plugin profesores por ID o coincidencia en nombre/apellido.
    """
    from plugins.profesores.backend.models import Profesor
    clean = nombre_o_id.strip()
    try:
        import uuid
        uid = uuid.UUID(clean)
        return Profesor.objects.filter(Q(id=uid) | Q(usuario_id=uid), is_active=True).first()
    except Exception:
        pass

    return Profesor.objects.filter(
        Q(nombre__icontains=clean) | Q(apellido__icontains=clean) | Q(usuario__nombre__icontains=clean),
        is_active=True
    ).first()


@tool
def consultar_mis_clases_profesor(profesor_usuario_id: str) -> str:
    """
    Retorna la lista de clases asignadas a una profesora o profesor para los próximos 7 días.
    """
    if not profesor_usuario_id:
        return "No estás identificada como profesora en el sistema."

    try:
        from plugins.profesores.backend.models import Profesor
        profe = buscar_profesor(profesor_usuario_id)
    except ImportError:
        return "El plugin de profesores no está habilitado."

    if not profe:
        return "No tenés un perfil docente activo en Violett Pilates."

    today = timezone.localdate()
    next_week = today + datetime.timedelta(days=7)

    turnos = Turno.objects.filter(
        Q(profesor_asignado__profesor=profe) | 
        (Q(profesor_asignado__isnull=True) & Q(plantilla__profesor_asignado__profesor=profe)),
        fecha__gte=today,
        fecha__lte=next_week,
        estado='PROGRAMADO'
    ).select_related('clase').order_by('fecha', 'hora_inicio').distinct()

    if not turnos.exists():
        return "No tenés clases asignadas programadas para los próximos 7 días."

    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    resultado = ["✦ Tus clases asignadas para los próximos días:"]
    for t in turnos:
        dia_nom = dias[t.fecha.weekday()]
        resultado.append(f"• {dia_nom} {t.fecha.strftime('%d/%m')} {t.hora_inicio.strftime('%H:%M')} hs - {t.clase.nombre} ({t.cupo_actual}/3 camillas libres) [ID Turno: {t.id}]")

    return "\n".join(resultado)


@tool
def reasignar_profesora_directo(fecha_o_dia: str, hora_str: str, profe_titular_nombre: str, nueva_profe_nombre: str) -> str:
    """
    Comando para la dueña del estudio: reasigna directamente un turno específico a una profesora de reemplazo.
    Ejemplo: 'El jueves a las 18 sacá a Cande y poné a Julieta'.
    Actualiza la base de datos y notifica por WhatsApp a ambas profesoras.
    """
    from ..models import RegistroAccionIA

    target_date = resolver_fecha(fecha_o_dia)
    target_time = resolver_hora(hora_str)

    # 1. Buscar turno
    qs_turnos = Turno.objects.filter(
        fecha=target_date,
        hora_inicio__hour=target_time.hour,
        estado='PROGRAMADO'
    ).select_related('clase')

    if not qs_turnos.exists():
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        dia_nom = dias[target_date.weekday()]
        return f"No encontré ninguna clase programada para el {dia_nom} {target_date.strftime('%d/%m')} a las {target_time.strftime('%H:%M')} hs."

    turno = None
    if profe_titular_nombre:
        profe_clean = profe_titular_nombre.strip().lower()
        for t in qs_turnos:
            p = obtener_profesor_de_turno(t)
            if p and profe_clean in (p.nombre + " " + p.apellido).lower():
                turno = t
                break
        if not turno:
            turno = qs_turnos.first()
    else:
        turno = qs_turnos.first()

    # 2. Buscar nueva profesora
    nueva_profe = buscar_profesor(nueva_profe_nombre)
    if not nueva_profe:
        return f"No se encontró en el staff a ninguna profesora llamada '{nueva_profe_nombre}'."

    # 3. Validar si la nueva profe ya tiene turno a esa hora
    conflicto = Turno.objects.filter(
        Q(profesor_asignado__profesor=nueva_profe) | 
        (Q(profesor_asignado__isnull=True) & Q(plantilla__profesor_asignado__profesor=nueva_profe)),
        fecha=turno.fecha,
        hora_inicio=turno.hora_inicio,
        estado='PROGRAMADO'
    ).exclude(id=turno.id).exists()

    if conflicto:
        return f"⚠️ Atención: {nueva_profe.nombre} ya tiene otra clase asignada en ese mismo horario ({turno.hora_inicio.strftime('%H:%M')} hs)."

    profe_anterior = obtener_profesor_de_turno(turno)
    nombre_anterior = f"{profe_anterior.nombre} {profe_anterior.apellido}".strip() if profe_anterior else "Sin asignar"
    nombre_nueva = f"{nueva_profe.nombre} {nueva_profe.apellido}".strip()

    # 4. Asignar nuevo profesor
    asignar_profesor_a_turno(turno, nueva_profe)

    # 5. Notificar a las profesoras vía WhatsApp
    client = WhatsAppClient()
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias[turno.fecha.weekday()]
    fecha_fmt = turno.fecha.strftime('%d/%m')
    hora_fmt = turno.hora_inicio.strftime('%H:%M')

    # A la nueva profesora
    tel_dest = (nueva_profe.telefono or (nueva_profe.usuario.telefono if nueva_profe.usuario else ""))
    if tel_dest:
        clean_dest = tel_dest.replace('+', '').replace(' ', '').replace('-', '')
        msg_nueva = (
            f"¡Hola {nueva_profe.nombre}! ✦ Te avisamos que la dirección te asignó la clase de "
            f"*{turno.clase.nombre}* del *{dia_nom} {fecha_fmt}* a las *{hora_fmt} hs*. ¡Muchas gracias!"
        )
        try:
            client.send_text_message(clean_dest, msg_nueva)
        except Exception as e:
            logger.warning(f"Error enviando WhatsApp a {nueva_profe.nombre}: {e}")

    # A la profesora reemplazada
    tel_ant = (profe_anterior.telefono if profe_anterior else None) or (profe_anterior.usuario.telefono if profe_anterior and profe_anterior.usuario else "")
    if tel_ant and (not profe_anterior or profe_anterior.id != nueva_profe.id):
        clean_ant = tel_ant.replace('+', '').replace(' ', '').replace('-', '')
        msg_ant = (
            f"Hola {profe_anterior.nombre}, te confirmamos que la dirección reasignó tu clase de "
            f"*{turno.clase.nombre}* del *{dia_nom} {fecha_fmt}* a las *{hora_fmt} hs* a *{nueva_profe.nombre}*."
        )
        try:
            client.send_text_message(clean_ant, msg_ant)
        except Exception as e:
            logger.warning(f"Error enviando WhatsApp a {profe_anterior.nombre}: {e}")

    # 6. Registrar acción de IA
    RegistroAccionIA.objects.create(
        tipo_accion='TURNO_REASIGNADO',
        descripcion=f"Reasignación directa: {turno.clase.nombre} ({dia_nom} {fecha_fmt} {hora_fmt}hs) de {nombre_anterior} a {nombre_nueva}.",
        payload={
            'turno_id': str(turno.id),
            'profe_anterior': nombre_anterior,
            'nueva_profe': nombre_nueva,
            'fecha': str(turno.fecha),
            'hora': str(turno.hora_inicio)
        }
    )

    return (
        f"✅ Clase reasignada con éxito:\n"
        f"• Clase: *{turno.clase.nombre}*\n"
        f"• Horario: *{dia_nom} {fecha_fmt} a las {hora_fmt} hs*\n"
        f"• Reemplazo: *{nombre_nueva}* sustituye a *{nombre_anterior}*\n"
        f"Ambas profesoras fueron notificadas por WhatsApp."
    )


@tool
def buscar_reemplazo_orden_duena(fecha_o_dia: str, hora_str: str, profe_titular_nombre: str = "") -> str:
    """
    Comando para la dueña del estudio: busca qué profesoras están disponibles para cubrir una clase y les envía una solicitud de reemplazo.
    Ejemplo: 'Fijate quién puede cubrir a Cande este martes a las 18'.
    """
    from ..models import RegistroAccionIA
    from plugins.profesores.backend.models import Profesor

    target_date = resolver_fecha(fecha_o_dia)
    target_time = resolver_hora(hora_str)

    qs_turnos = Turno.objects.filter(
        fecha=target_date,
        hora_inicio__hour=target_time.hour,
        estado='PROGRAMADO'
    ).select_related('clase')

    if not qs_turnos.exists():
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        dia_nom = dias[target_date.weekday()]
        return f"No encontré turnos programados para el {dia_nom} {target_date.strftime('%d/%m')} a las {target_time.strftime('%H:%M')} hs."

    turno = qs_turnos.first()
    profe_titular = obtener_profesor_de_turno(turno)
    nombre_titular = f"{profe_titular.nombre} {profe_titular.apellido}".strip() if profe_titular else "La profesora titular"

    # Buscar otras profesoras activas del staff
    otros_profes = Profesor.objects.filter(is_active=True)
    if profe_titular:
        otros_profes = otros_profes.exclude(id=profe_titular.id)

    # Identificar quiénes no tienen clase en esa misma franja
    candidatas = []
    for p in otros_profes:
        tiene_clase = Turno.objects.filter(
            Q(profesor_asignado__profesor=p) | 
            (Q(profesor_asignado__isnull=True) & Q(plantilla__profesor_asignado__profesor=p)),
            fecha=turno.fecha,
            hora_inicio=turno.hora_inicio,
            estado='PROGRAMADO'
        ).exists()
        tel = p.telefono or (p.usuario.telefono if p.usuario else None)
        if not tiene_clase and tel:
            candidatas.append(p)

    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias[turno.fecha.weekday()]
    fecha_fmt = turno.fecha.strftime('%d/%m')
    hora_fmt = turno.hora_inicio.strftime('%H:%M')

    if not candidatas:
        return f"⚠️ No encontré profesoras del staff con disponibilidad libre para el {dia_nom} {fecha_fmt} a las {hora_fmt} hs. Todas tienen clases asignadas en esa misma hora."

    # Enviar WhatsApp a las disponibles
    client = WhatsAppClient()
    nombres_contactadas = []
    for p in candidatas:
        tel = p.telefono or (p.usuario.telefono if p.usuario else None)
        clean_phone = tel.replace('+', '').replace(' ', '').replace('-', '')
        msg = (
            f"¡Hola {p.nombre}! ✦ Consulta de la dirección: se necesita suplente para la clase de "
            f"*{turno.clase.nombre}* del *{dia_nom} {fecha_fmt}* a las *{hora_fmt} hs* (titular: {nombre_titular}).\n\n"
            f"¿Podrías darla? Si podés, respondeme *'Sí puedo cubrir'* y te la asigno."
        )
        try:
            client.send_text_message(clean_phone, msg)
            nombres_contactadas.append(f"{p.nombre}")
        except Exception as e:
            logger.warning(f"Error enviando solicitud a {p.nombre}: {e}")

    RegistroAccionIA.objects.create(
        tipo_accion='TURNO_REASIGNADO',
        descripcion=f"Búsqueda por orden de la dueña: {turno.clase.nombre} ({dia_nom} {fecha_fmt} {hora_fmt}hs). Contactadas: {', '.join(nombres_contactadas)}.",
        payload={'turno_id': str(turno.id), 'contactadas': nombres_contactadas}
    )

    return (
        f"✦ Búsqueda de reemplazo iniciada para el *{dia_nom} {fecha_fmt} {hora_fmt} hs*:\n"
        f"Encontré {len(candidatas)} profesoras con disponibilidad libre: *{', '.join(nombres_contactadas)}*.\n"
        f"Ya les envié un mensaje por WhatsApp. En cuanto alguna confirme, te aviso y queda reasignada automáticamente."
    )


@tool
def gestionar_ausencia_y_buscar_reemplazo(profesor_usuario_id: str, turno_id: str, motivo: str = "") -> str:
    """
    Permite a una profesora avisar que no puede dar una clase.
    El sistema busca automáticamente a otras profesoras activas del staff que no tengan clase asignada en ese horario
    y les envía una solicitud de guardia/reemplazo por WhatsApp.
    """
    from ..models import RegistroAccionIA
    from plugins.profesores.backend.models import Profesor

    if not profesor_usuario_id or not turno_id:
        return "Se necesita el ID de la profesora y el ID del turno a cubrir."

    try:
        turno = Turno.objects.select_related('clase').get(id=turno_id)
    except Turno.DoesNotExist:
        return "El turno especificado no existe."

    profe_titular = obtener_profesor_de_turno(turno) or buscar_profesor(profesor_usuario_id)
    nombre_titular = f"{profe_titular.nombre} {profe_titular.apellido}".strip() if profe_titular else "Una profesora"

    otros_profes = Profesor.objects.filter(is_active=True)
    if profe_titular:
        otros_profes = otros_profes.exclude(id=profe_titular.id)

    candidatas = []
    for p in otros_profes:
        tiene_clase = Turno.objects.filter(
            Q(profesor_asignado__profesor=p) | 
            (Q(profesor_asignado__isnull=True) & Q(plantilla__profesor_asignado__profesor=p)),
            fecha=turno.fecha,
            hora_inicio=turno.hora_inicio,
            estado='PROGRAMADO'
        ).exists()
        tel = p.telefono or (p.usuario.telefono if p.usuario else None)
        if not tiene_clase and tel:
            candidatas.append(p)

    if not candidatas:
        config = get_asistente_config()
        tel_duena = config.get('telefono_duena')
        if tel_duena:
            client = WhatsAppClient()
            client.send_text_message(
                tel_duena,
                f"⚠️ AVISO URGENTE: {nombre_titular} no puede dar la clase de {turno.clase.nombre} del {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs (Motivo: {motivo or 'No especificado'}). No se encontraron profesoras disponibles en el staff."
            )
        return f"Entendido, registré tu aviso de ausencia. No encontré profesoras con disponibilidad libre para ese bloque, así que ya le notifiqué con urgencia a la dirección del estudio para coordinar la cobertura."

    client = WhatsAppClient()
    contactadas = []
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias[turno.fecha.weekday()]

    for p in candidatas:
        tel = p.telefono or (p.usuario.telefono if p.usuario else None)
        clean_phone = tel.replace('+', '').replace(' ', '').replace('-', '')
        nombre_p = p.nombre or "profe"
        msg = (
            f"¡Hola {nombre_p}! ✦ {nombre_titular} no va a poder dar la clase de {turno.clase.nombre} "
            f"del {dia_nom} {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs. "
            f"¿Tendrías disponibilidad para cubrirla? Si podés, respondé 'Sí puedo cubrir' y te la asigno."
        )
        try:
            client.send_text_message(clean_phone, msg)
            contactadas.append(f"{p.nombre} ({tel})")
        except Exception as e:
            logger.warning(f"Error enviando mensaje a {p.nombre}: {e}")

    RegistroAccionIA.objects.create(
        tipo_accion='TURNO_REASIGNADO',
        descripcion=f"Búsqueda de reemplazo iniciada para clase {turno.clase.nombre} ({turno.fecha} {turno.hora_inicio}). Contactadas: {len(contactadas)} profesoras.",
        payload={'turno_id': str(turno.id), 'contactadas': contactadas, 'motivo': motivo}
    )

    return f"✦ Listo, no te preocupes. Ya le envié un mensaje a {len(contactadas)} profesoras del staff que están libres en ese horario para coordinar la suplencia. Apenas alguna confirme, queda reasignada y te avisamos."
