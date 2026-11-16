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

    # Formato ISO primero: YYYY-MM-DD
    m_iso = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', s)
    if m_iso:
        try:
            return datetime.date(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
        except ValueError:
            pass

    # Formato latino: DD/MM o DD/MM/YYYY
    m = re.search(r'(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?', s)
    if m:
        try:
            day = int(m.group(1))
            month = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else today.year
            if year < 100:
                year += 2000
            return datetime.date(year, month, day)
        except ValueError:
            pass

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


@tool("reasignar_todas_las_clases_profesor_duena")
def reasignar_todas_las_clases_profesor_duena(profe_saliente_nombre: str, nueva_profe_nombre: str) -> str:
    """
    Comando para la dueña del estudio (Deby): reasigna de forma MASIVA e INMEDIATA todas las clases de un profesor/a saliente
    a una nueva profesora de reemplazo, sincronizando en conjunto tanto el ESQUEMA SEMANAL (grilla fija recurrente)
    como la AGENDA de clases futuras (desde hoy en adelante).

    Parámetros:
    - profe_saliente_nombre: Nombre del profesor a reemplazar (ej: 'Brian Agüero', 'Brian').
    - nueva_profe_nombre: Nombre de la profesora que asume todas las clases (ej: 'Emiliana Gauna', 'Emiliana').
    """
    from ..models import RegistroAccionIA
    from plugins.profesores.backend.models import Profesor, PlantillaProfesor, TurnoProfesor
    from core.models import PlantillaTurno, Turno

    profe_saliente = buscar_profesor(profe_saliente_nombre)
    if not profe_saliente:
        return f"✦ No encontré en el staff a ningún profesor/a llamado '{profe_saliente_nombre}'."

    nueva_profe = buscar_profesor(nueva_profe_nombre)
    if not nueva_profe:
        return f"✦ No encontré en el staff a ninguna profesora llamada '{nueva_profe_nombre}'."

    nom_saliente = f"{profe_saliente.nombre} {profe_saliente.apellido}".strip()
    nom_nueva = f"{nueva_profe.nombre} {nueva_profe.apellido}".strip()

    # 1. Actualizar Esquema Semanal (Plantillas fijas recurrentes)
    plantillas_mod = PlantillaProfesor.objects.filter(profesor=profe_saliente)
    total_plantillas = plantillas_mod.count()
    plantillas_mod.update(profesor=nueva_profe)

    # 2. Actualizar Agenda de clases futuras (desde hoy en adelante)
    hoy = timezone.localdate()
    turnos_prof_qs = TurnoProfesor.objects.filter(
        profesor=profe_saliente,
        turno__fecha__gte=hoy
    ).exclude(turno__estado='CANCELADO')
    total_turnos = turnos_prof_qs.count()
    turnos_prof_qs.update(profesor=nueva_profe)

    # 3. Asegurar que cualquier turno futuro cuya plantilla tenga a la nueva profe quede asignado
    plantillas_nueva_ids = PlantillaProfesor.objects.filter(profesor=nueva_profe).values_list('plantilla_id', flat=True)
    turnos_de_plantilla = Turno.objects.filter(
        plantilla_id__in=plantillas_nueva_ids,
        fecha__gte=hoy
    ).exclude(estado='CANCELADO')
    for t in turnos_de_plantilla:
        TurnoProfesor.objects.update_or_create(
            turno=t,
            defaults={'profesor': nueva_profe}
        )

    # 4. Sincronizar cualquier turno futuro coincidente con las plantillas
    for pp in PlantillaProfesor.objects.filter(profesor=nueva_profe).select_related('plantilla'):
        t_coincidentes = Turno.objects.filter(
            clase=pp.plantilla.clase,
            hora_inicio=pp.plantilla.hora_inicio,
            fecha__gte=hoy
        ).exclude(estado='CANCELADO')
        for tc in t_coincidentes:
            if tc.fecha.isoweekday() == pp.plantilla.dia_semana:
                TurnoProfesor.objects.update_or_create(
                    turno=tc,
                    defaults={'profesor': nueva_profe}
                )

    # 5. Notificar a las profesoras vía WhatsApp si corresponde
    client = WhatsAppClient()
    tel_nueva = (nueva_profe.telefono or (nueva_profe.usuario.telefono if nueva_profe.usuario else ""))
    if tel_nueva:
        clean_nueva = tel_nueva.replace('+', '').replace(' ', '').replace('-', '')
        msg_nueva = (
            f"¡Hola {nueva_profe.nombre}! ✦ Te informamos que la dirección te reasignó todas las clases de "
            f"*{nom_saliente}* a tu cargo, tanto en el Esquema Semanal como en la Agenda de clases futuras. ¡Muchas gracias!"
        )
        try:
            client.send_text_message(clean_nueva, msg_nueva)
        except Exception:
            pass

    tel_sal = (profe_saliente.telefono or (profe_saliente.usuario.telefono if profe_saliente.usuario else ""))
    if tel_sal and profe_saliente.id != nueva_profe.id:
        clean_sal = tel_sal.replace('+', '').replace(' ', '').replace('-', '')
        msg_sal = (
            f"Hola {profe_saliente.nombre}, te confirmamos que la dirección reasignó todas tus clases "
            f"a cargo de *{nom_nueva}* en el sistema."
        )
        try:
            client.send_text_message(clean_sal, msg_sal)
        except Exception:
            pass

    # 6. Registrar en auditoría
    RegistroAccionIA.objects.create(
        tipo_accion='REASIGNACION_MASIVA_PROFESOR',
        descripcion=f"Reasignación masiva de todas las clases de {nom_saliente} a {nom_nueva} en Esquema ({total_plantillas}) y Agenda ({total_turnos}).",
        payload={
            'profe_saliente': nom_saliente,
            'nueva_profe': nom_nueva,
            'plantillas_actualizadas': total_plantillas,
            'turnos_actualizados': total_turnos
        }
    )

    return (
        f"✅ **¡Listo Deby! Sincronicé todas las clases de {nom_saliente} a cargo de {nom_nueva} en conjunto:**\n\n"
        f"• **Esquema Semanal:** {total_plantillas} horarios recurrentes fijados con {nom_nueva}.\n"
        f"• **Agenda de clases:** Todas las clases futuras (a partir de hoy {hoy.strftime('%d/%m')}) quedaron a cargo de {nom_nueva}.\n\n"
        f"El cambio ya se encuentra 100% visible tanto en el Esquema como en la Agenda del panel web."
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


@tool
def registrar_asistencia_clase_profesor(
    todas_presentes: bool = False,
    alumnas_ausentes: str = "",
    alumnas_presentes: str = "",
    turno_id: str = "",
    profesor_usuario_id: str = "",
    fecha_o_dia: str = "hoy",
    hora_str: str = ""
) -> str:
    """
    Registra la asistencia de las alumnas de una clase dictada por una profesora o profesor.
    Parámetros:
    - todas_presentes: True si todas las alumnas de la clase asistieron (ej: 'Vinieron todas', 'Todas presentes', 'Estuvieron todas').
    - alumnas_ausentes: Nombres de las alumnas que faltaron separados por coma (ej: 'Nora, Gladys' o 'faltó Marcela').
    - alumnas_presentes: Nombres de las alumnas que sí vinieron si fue solo un subgrupo (ej: 'vino solo Laura').
    - turno_id: Opcional, ID exacto del turno a marcar. Si no se pasa, busca la clase pendiente más reciente de la profesora hoy.
    - profesor_usuario_id: Opcional, ID de la profesora.
    - hora_str: Opcional, horario de la clase (ej: '18:00', '18hs').
    """
    from core.models import Turno, Reserva, LogMovimientoClase
    from ..models import RegistroAccionIA, ConversacionWhatsApp
    from plugins.profesores.backend.models import Profesor

    today = resolver_fecha(fecha_o_dia)
    now = timezone.localtime()

    # 1. Resolver el Turno
    turno = None
    if turno_id:
        try:
            turno = Turno.objects.select_related('clase', 'plantilla').prefetch_related('reservas', 'reservas__usuario').get(id=turno_id)
        except Exception:
            turno = None

    if not turno and hora_str:
        target_time = resolver_hora(hora_str)
        turno = Turno.objects.filter(
            fecha=today,
            hora_inicio__hour=target_time.hour,
            estado__in=['PROGRAMADO', 'COMPLETADO']
        ).select_related('clase', 'plantilla').prefetch_related('reservas', 'reservas__usuario').first()

    # Si aún no tenemos turno, buscar en las clases asignadas al profesor hoy que tengan reservas 'CONFIRMADA' o terminaron
    if not turno:
        profe = None
        if profesor_usuario_id:
            profe = buscar_profesor(profesor_usuario_id)

        qs = Turno.objects.filter(
            fecha=today,
            estado__in=['PROGRAMADO', 'COMPLETADO']
        ).select_related('clase', 'plantilla').prefetch_related('reservas', 'reservas__usuario').order_by('-hora_inicio')

        if profe:
            qs = qs.filter(
                Q(profesor_asignado__profesor=profe) |
                (Q(profesor_asignado__isnull=True) & Q(plantilla__profesor_asignado__profesor=profe))
            )

        # Priorizar aquel turno que tenga reservas 'CONFIRMADA'
        for t in qs:
            if t.reservas.filter(estado='CONFIRMADA').exists():
                turno = t
                break

        # Si ninguno tiene CONFIRMADA, tomar el último de hoy
        if not turno and qs.exists():
            turno = qs.first()

    if not turno:
        return "No encontré ninguna clase pendiente de asistencia para hoy. Por favor indicame el horario de la clase (ej: 'la clase de las 18hs')."

    reservas = list(turno.reservas.exclude(estado__in=['CANCELADA_TIEMPO', 'CANCELADA_TARDIA']).select_related('usuario'))
    if not reservas:
        return f"La clase de {turno.clase.nombre} ({turno.hora_inicio.strftime('%H:%M')} hs) no tenía alumnas inscriptas."

    profe_obj = obtener_profesor_de_turno(turno)
    nombre_profe = f"{profe_obj.nombre} {profe_obj.apellido}".strip() if profe_obj else "Profesor/a"

    resumen_cambios = []
    ausentes_tokens = [a.strip().lower() for a in alumnas_ausentes.replace(' y ', ',').split(',') if a.strip()]
    presentes_tokens = [p.strip().lower() for p in alumnas_presentes.replace(' y ', ',').split(',') if p.strip()]

    for r in reservas:
        nom_alumna = f"{r.usuario.nombre} {r.usuario.apellido}".strip() if r.usuario else (r.nombre_temporal or "Alumna")
        nom_low = nom_alumna.lower()
        estado_ant = r.estado

        if todas_presentes:
            nuevo_st = 'TOMADA'
        elif ausentes_tokens:
            is_ausente = any(tok in nom_low for tok in ausentes_tokens)
            nuevo_st = 'AUSENTE' if is_ausente else 'TOMADA'
        elif presentes_tokens:
            is_presente = any(tok in nom_low for tok in presentes_tokens)
            nuevo_st = 'TOMADA' if is_presente else 'AUSENTE'
        else:
            nuevo_st = 'TOMADA'

        r.estado = nuevo_st
        r.modificada_manualmente = True
        r.modificada_por = f"{nombre_profe} (WhatsApp)"
        r.motivo_modificacion = f"Asistencia reportada por WhatsApp por {nombre_profe}"
        r.fecha_modificacion = timezone.now()
        r.save(update_fields=['estado', 'modificada_manualmente', 'modificada_por', 'motivo_modificacion', 'fecha_modificacion'])

        # Registrar log de auditoría
        if r.usuario:
            LogMovimientoClase.objects.create(
                reserva=r,
                usuario=r.usuario,
                turno=turno,
                tipo_movimiento='ASISTENCIA_REGISTRADA_WPP',
                estado_anterior=estado_ant,
                estado_nuevo=nuevo_st,
                realizado_por=f"{nombre_profe} (WhatsApp)",
                motivo="Asistencia informada por mensaje de WhatsApp"
            )

        simbolo = "✓ Presente" if nuevo_st == 'TOMADA' else "✕ Ausente"
        resumen_cambios.append(f"• {nom_alumna}: {simbolo}")

    # Si ya no quedan reservas pendientes, marcar turno como COMPLETADO
    if not turno.reservas.filter(estado='CONFIRMADA').exists():
        turno.estado = 'COMPLETADO'
        turno.save(update_fields=['estado'])

    # Registrar acción de IA
    RegistroAccionIA.objects.create(
        tipo_accion='ASISTENCIA_REGISTRADA',
        descripcion=f"Asistencia tomada vía WhatsApp para {turno.clase.nombre} ({turno.fecha} {turno.hora_inicio.strftime('%H:%M')}hs) por {nombre_profe}.",
        payload={
            'turno_id': str(turno.id),
            'profe': nombre_profe,
            'cambios': resumen_cambios
        }
    )

    hora_fmt = turno.hora_inicio.strftime('%H:%M')
    resumen_txt = "\n".join(resumen_cambios)
    return (
        f"✅ ¡Excelente {nombre_profe.split()[0]}! Ya quedó registrada la asistencia de la clase de *{turno.clase.nombre}* de las *{hora_fmt} hs*:\n\n"
        f"{resumen_txt}\n\n"
        f"¡Muchas gracias por mantener la agenda al día! ✨"
    )


@tool
def consultar_clases_sin_asistencia_hoy() -> str:
    """
    Lista todas las clases dictadas hoy que aún tienen alumnas con reserva 'CONFIRMADA' (asistencia sin tomar).
    Muestra la clase, el horario, el profesor a cargo y los nombres de las alumnas pendientes.
    """
    from core.models import Turno
    today = timezone.localdate()
    now_time = timezone.localtime().time()

    turnos_pendientes = Turno.objects.filter(
        fecha=today,
        hora_fin__lte=now_time,
        estado='PROGRAMADO',
        reservas__estado='CONFIRMADA'
    ).select_related('clase', 'plantilla').prefetch_related('reservas', 'reservas__usuario').distinct().order_by('hora_inicio')

    if not turnos_pendientes.exists():
        return "✦ ¡Excelente! No hay ninguna clase pendiente de asistencia el día de hoy. Todas las clases finalizadas tienen su asistencia completa."

    lineas = ["📋 **Clases de hoy con asistencia pendiente de marcar:**\n"]
    for t in turnos_pendientes:
        prof = obtener_profesor_de_turno(t)
        nom_prof = f"{prof.nombre} {prof.apellido}".strip() if prof else "Sin profesor asignado"
        hora_fmt = t.hora_inicio.strftime('%H:%M')
        reservas_conf = t.reservas.filter(estado='CONFIRMADA')
        alumnas_noms = [
            f"{r.usuario.nombre} {r.usuario.apellido}".strip() if r.usuario else (r.nombre_temporal or 'Alumna')
            for r in reservas_conf
        ]
        lineas.append(f"• **{hora_fmt} hs** — {t.clase.nombre} (Prof: *{nom_prof}*): {len(alumnas_noms)} alumnas ({', '.join(alumnas_noms)})")

    return "\n".join(lineas)
