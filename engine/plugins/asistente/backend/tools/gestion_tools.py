import datetime
import logging
import re
from django.utils import timezone
from django.db.models import Q
from langchain_core.tools import tool

from core.models import Usuario, Turno, Reserva
from .profesores_tools import resolver_fecha

logger = logging.getLogger(__name__)

def buscar_alumna_flexible(query: str):
    """
    Busca una alumna por nombre, apellido o teléfono de manera tolerante a mayúsculas y acentos.
    Retorna (alumna_encontrada, lista_coincidencias, error_str).
    """
    q_clean = query.strip()
    if not q_clean:
        return None, [], "No se especificó el nombre o teléfono de la alumna."

    # Si es teléfono numérico
    solo_num = re.sub(r'\D', '', q_clean)
    if len(solo_num) >= 6:
        ultimos = solo_num[-8:]
        qs = Usuario.objects.filter(telefono__icontains=ultimos)
        if qs.count() == 1:
            return qs.first(), [qs.first()], None
        elif qs.count() > 1:
            return None, list(qs), "multiples"

    # Buscar por palabras del nombre / apellido
    palabras = [p for p in q_clean.split() if len(p) >= 2 and p.lower() not in ['alumna', 'la', 'el', 'a', 'de']]
    if not palabras:
        palabras = [q_clean]

    filtro = Q()
    for p in palabras:
        filtro |= Q(nombre__icontains=p) | Q(apellido__icontains=p) | Q(email__icontains=p)

    qs = Usuario.objects.filter(filtro).exclude(rol='PROFESOR').distinct()
    
    # Si no hubo resultado con OR amplio, probar si coinciden nombre y apellido juntos
    if not qs.exists():
        qs = Usuario.objects.filter(
            Q(nombre__icontains=q_clean) | Q(apellido__icontains=q_clean)
        ).distinct()

    cant = qs.count()
    if cant == 0:
        return None, [], f"No encontré ninguna alumna registrada con '{q_clean}' en el sistema."
    elif cant == 1:
        return qs.first(), list(qs), None
    else:
        # Si una de las coincidencias tiene el nombre completo exacto, priorizarla
        for u in qs:
            nom_comp = f"{u.nombre} {u.apellido}".lower()
            if q_clean.lower() in nom_comp or nom_comp in q_clean.lower():
                return u, [u], None
        return None, list(qs), "multiples"


@tool
def renovar_o_asignar_plan_alumna(nombre_o_tel_alumna: str, nombre_o_clases_plan: str = "") -> str:
    """
    Comando exclusivo de la dueña (Deby) para renovar o cargar un abono/plan a una alumna desde WhatsApp.
    Parámetros:
    - nombre_o_tel_alumna: Nombre, apellido o teléfono de la alumna (ej: 'Laila Marzzuck', 'Marcela').
    - nombre_o_clases_plan: Cantidad de clases o nombre del plan (ej: '8', 'Plan 8 clases', '4', '12').
      Si se deja vacío, renueva automáticamente el mismo plan que la alumna ya venía teniendo.
    """
    try:
        from plugins.membresias.backend.models import Plan, Suscripcion
    except ImportError:
        return "El módulo de membresías no está disponible en este momento."

    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        nombres = [f"• {u.nombre} {u.apellido} (Tel: {u.telefono or 'Sin tel'})" for u in matches[:4]]
        return f"✦ Encontré más de una alumna con ese nombre:\n" + "\n".join(nombres) + "\n\n¿A cuál de ellas querés que le renueve el abono?"
    elif not alumna:
        return f"✦ No encontré a ninguna alumna registrada como '{nombre_o_tel_alumna}' en Violett Pilates. Verificá cómo figura su nombre o pasame su número de teléfono."

    # Identificar el Plan a asignar
    plan_seleccionado = None
    if nombre_o_clases_plan:
        txt_plan = str(nombre_o_clases_plan).strip().lower()
        num_match = re.search(r'\b(1|4|8|12|16)\b', txt_plan)
        if num_match:
            cant_clases = int(num_match.group(1))
            plan_seleccionado = Plan.objects.filter(is_active=True, cantidad_clases=cant_clases).first()
        if not plan_seleccionado:
            plan_seleccionado = Plan.objects.filter(is_active=True, nombre__icontains=txt_plan).first()

    # Si no se especificó o no se encontró, tomar el último plan que tuvo la alumna
    if not plan_seleccionado:
        ultima_sub = Suscripcion.objects.filter(usuario=alumna).select_related('plan').order_by('-fecha_inicio').first()
        if ultima_sub and ultima_sub.plan and ultima_sub.plan.is_active:
            plan_seleccionado = ultima_sub.plan
        else:
            # Plan estándar por defecto (8 clases)
            plan_seleccionado = Plan.objects.filter(is_active=True, cantidad_clases=8).first() or Plan.objects.filter(is_active=True).first()

    if not plan_seleccionado:
        return "No hay planes activos configurados en el sistema para poder asignar."

    hoy = timezone.localdate()
    vencimiento = hoy + datetime.timedelta(days=30)

    # 1. Vencer suscripciones activas anteriores
    Suscripcion.objects.filter(usuario=alumna, estado__in=['ACTIVO', 'AGOTADO']).update(estado='VENCIDO')

    # 2. Crear nueva suscripción activa
    nueva_sub = Suscripcion.objects.create(
        usuario=alumna,
        plan=plan_seleccionado,
        clases_restantes=plan_seleccionado.cantidad_clases,
        fecha_inicio=hoy,
        fecha_vencimiento=vencimiento,
        estado='ACTIVO'
    )

    # 3. Disparar hooks de eventos (para webhooks, notificaciones y analítica)
    try:
        from backend_core.hooks import registry
        registry.execute('plan_asignado', data={'suscripcion': nueva_sub, 'usuario': alumna, 'plan': plan_seleccionado})
    except Exception as e:
        logger.warning(f"Error ejecutando hook 'plan_asignado': {e}")

    # 4. Auto-agendar en turnos recurrentes fijos si la alumna tiene esquema configurado
    reservas_agendadas = 0
    try:
        from plugins.recurrencias.backend.services import auto_agendar_recurrencias_usuario
        reservas_agendadas = auto_agendar_recurrencias_usuario(alumna, nueva_sub)
    except Exception as e:
        logger.warning(f"Error auto-agendando recurrencias: {e}")

    nueva_sub.refresh_from_db()
    nombre_completo = f"{alumna.nombre} {alumna.apellido}".strip() or alumna.email.split('@')[0]
    precio_str = f"${plan_seleccionado.precio:,.0f}".replace(",", ".") if hasattr(plan_seleccionado, 'precio') and plan_seleccionado.precio else "Consultar"

    return f"""✦ ¡Listo Deby! Le renové el plan a {nombre_completo}:
• Plan acreditado: {plan_seleccionado.nombre} ({precio_str})
• Créditos cargados: {plan_seleccionado.cantidad_clases} clases
• Créditos libres disponibles: {nueva_sub.clases_restantes}
• Clases fijas agendadas automáticamente: {reservas_agendadas}
• Vigencia: Hasta el {vencimiento.strftime('%d/%m/%Y')} (30 días)

El abono ya quedó registrado y activo en el sistema 🌸."""


@tool
def consultar_alumna_detalle(nombre_o_tel: str) -> str:
    """
    Comando para la dueña: busca a una alumna y muestra su estado completo:
    plan actual, clases disponibles, vencimiento, teléfono y sus próximas clases reservadas.
    NUNCA inventa datos: si no existe, avisa que no fue encontrada.
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel)
    if err == "multiples":
        nombres = [f"• {u.nombre} {u.apellido} ({u.telefono or 'Sin tel'})" for u in matches[:5]]
        return f"✦ Encontré más de una alumna con ese criterio:\n" + "\n".join(nombres) + "\n\n¿De cuál querés ver los datos?"
    elif not alumna:
        return f"✦ No encontré a ninguna alumna registrada con '{nombre_o_tel}' en la base de datos."

    nombre_completo = f"{alumna.nombre} {alumna.apellido}".strip()
    tel = alumna.telefono or "No registrado"
    email = alumna.email

    from plugins.membresias.backend.models import Suscripcion
    sub = Suscripcion.objects.filter(usuario=alumna, estado__in=['ACTIVO', 'AGOTADO']).select_related('plan').first()
    
    if sub:
        info_plan = f"• Plan actual: {sub.plan.nombre}\n• Créditos restantes: {sub.clases_restantes}\n• Vence: {sub.fecha_vencimiento.strftime('%d/%m/%Y')}\n• Estado: {sub.estado}"
    else:
        info_plan = "• Plan actual: Sin plan activo actualmente."

    today = timezone.localdate()
    futuras = Reserva.objects.filter(
        usuario=alumna,
        turno__fecha__gte=today,
        estado='CONFIRMADA'
    ).select_related('turno', 'turno__profesor').order_by('turno__fecha', 'turno__hora_inicio')[:5]

    if futuras.exists():
        dias_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        lista_turnos = []
        for r in futuras:
            t = r.turno
            dia_str = dias_es[t.fecha.weekday()]
            profe = f" (Profe: {t.profesor.nombre})" if t.profesor else ""
            lista_turnos.append(f"  • {dia_str} {t.fecha.strftime('%d/%m')} a las {t.hora_inicio.strftime('%H:%M')} hs{profe}")
        info_turnos = "Próximas clases agendadas:\n" + "\n".join(lista_turnos)
    else:
        info_turnos = "Próximas clases: No tiene turnos reservados próximamente."

    return f"""✦ Ficha de Alumna: {nombre_completo}
• Teléfono: {tel}
• Email: {email}
{info_plan}

{info_turnos}"""


@tool
def agendar_alumna_en_turno_duena(nombre_o_tel_alumna: str, fecha_o_dia: str, hora_str: str) -> str:
    """
    Comando para la dueña: inscribe manualmente a una alumna en una camilla de un turno específico.
    Parámetros:
    - nombre_o_tel_alumna: Nombre o teléfono de la alumna (ej: 'Laila Marzzuck').
    - fecha_o_dia: 'hoy', 'mañana' o nombre del día (ej: 'jueves', 'viernes').
    - hora_str: Hora de inicio (ej: '18:00', '19', '20').
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return f"Encontré varias alumnas con ese nombre. Por favor especificá el apellido completo o teléfono."
    elif not alumna:
        return f"No encontré a la alumna '{nombre_o_tel_alumna}' en el sistema."

    target_date = resolver_fecha(fecha_o_dia)
    hora_clean = hora_str.lower().replace('hs', '').replace('h', '').strip()
    if ':' not in hora_clean:
        try:
            hora_clean = f"{int(hora_clean):02d}:00"
        except ValueError:
            hora_clean = "18:00"

    turnos = Turno.objects.filter(
        fecha=target_date,
        hora_inicio__startswith=hora_clean,
        estado='PROGRAMADO'
    ).select_related('profesor')

    if not turnos.exists():
        return f"No encontré ninguna clase programada para el {target_date.strftime('%d/%m/%Y')} a las {hora_clean} hs."

    turno = turnos.first()

    # Verificar si ya está anotada
    if Reserva.objects.filter(turno=turno, usuario=alumna, estado='CONFIRMADA').exists():
        return f"{alumna.nombre} ya tiene una camilla reservada en ese horario ({target_date.strftime('%d/%m')} a las {hora_clean} hs)."

    if turno.cupo_actual <= 0:
        return f"La clase del {target_date.strftime('%d/%m')} a las {hora_clean} hs ya tiene sus 3 camillas completas."

    # Verificar membresía
    from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
    sub = Suscripcion.objects.filter(usuario=alumna, estado__in=['ACTIVO', 'AGOTADO']).first()

    reserva = Reserva.objects.create(
        turno=turno,
        usuario=alumna,
        estado='CONFIRMADA'
    )
    turno.cupo_actual -= 1
    turno.save()

    if sub:
        ReservaMembresia.objects.create(reserva=reserva, suscripcion=sub)
        if sub.clases_restantes > 0:
            sub.clases_restantes -= 1
            if sub.clases_restantes == 0:
                sub.estado = 'AGOTADO'
            sub.save()

    nombre_completo = f"{alumna.nombre} {alumna.apellido}".strip()
    profe_str = f" con la profe {turno.profesor.nombre}" if turno.profesor else ""
    return f"✦ ¡Listo Deby! Anoté a {nombre_completo} para el {target_date.strftime('%d/%m/%Y')} a las {turno.hora_inicio.strftime('%H:%M')} hs{profe_str}. Quedan {turno.cupo_actual} camilla(s) libre(s) en ese bloque."


@tool
def cancelar_reserva_alumna_duena(nombre_o_tel_alumna: str, fecha_o_dia: str = "hoy", hora_str: str = "") -> str:
    """
    Comando para la dueña: cancela la reserva de una alumna en una clase específica y libera la camilla.
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if not alumna:
        return f"No encontré a la alumna '{nombre_o_tel_alumna}' en el sistema."

    target_date = resolver_fecha(fecha_o_dia)
    qs = Reserva.objects.filter(
        usuario=alumna,
        turno__fecha=target_date,
        estado='CONFIRMADA'
    ).select_related('turno')

    if hora_str:
        h = hora_str.replace('hs', '').strip()
        qs = qs.filter(turno__hora_inicio__startswith=h)

    if not qs.exists():
        return f"No encontré ninguna reserva confirmada de {alumna.nombre} para el {target_date.strftime('%d/%m/%Y')}."

    reserva = qs.first()
    turno = reserva.turno
    reserva.estado = 'CANCELADA_TIEMPO'
    reserva.save()

    turno.cupo_actual = min(3, turno.cupo_actual + 1)
    turno.save()

    # Reintegrar crédito a la alumna
    from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
    ReservaMembresia.objects.filter(reserva=reserva).delete()
    sub = Suscripcion.objects.filter(usuario=alumna, estado__in=['ACTIVO', 'AGOTADO']).first()
    if sub:
        sub.clases_restantes += 1
        sub.estado = 'ACTIVO'
        sub.save()

    nombre_completo = f"{alumna.nombre} {alumna.apellido}".strip()
    return f"✦ Cancelé la reserva de {nombre_completo} del {target_date.strftime('%d/%m/%Y')} a las {turno.hora_inicio.strftime('%H:%M')} hs. Se liberó la camilla (ahora hay {turno.cupo_actual} libres) y se le reintegró su crédito."


@tool
def consultar_agenda_completa_dia(fecha_o_dia: str = "hoy") -> str:
    """
    Comando para la dueña: muestra la grilla completa de clases del día con los nombres de las alumnas
    anotadas en cada camilla, profesoras a cargo y camillas vacías.
    """
    target_date = resolver_fecha(fecha_o_dia)
    dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias_es[target_date.weekday()]

    turnos = Turno.objects.filter(
        fecha=target_date,
        estado='PROGRAMADO'
    ).select_related('profesor').prefetch_related('reservas__usuario').order_by('hora_inicio')

    if not turnos.exists():
        return f"No hay turnos programados en la agenda para el {dia_nom} {target_date.strftime('%d/%m/%Y')}."

    lineas = [f"✦ Agenda de Violett Pilates - {dia_nom} {target_date.strftime('%d/%m/%Y')}:"]
    for t in turnos:
        profe = f" | Profe: {t.profesor.nombre}" if t.profesor else ""
        reservas = [r for r in t.reservas.all() if r.estado == 'CONFIRMADA']
        cant = len(reservas)
        nombres = [f"{r.usuario.nombre} {r.usuario.apellido}".strip() for r in reservas]
        nombres_str = ", ".join(nombres) if nombres else "Sin alumnas aún"
        libres = 3 - cant
        lineas.append(f"• {t.hora_inicio.strftime('%H:%M')} hs ({cant}/3 ocupadas){profe}\n  Alumnas: {nombres_str} ({libres} camilla(s) libre(s))")

    return "\n\n".join(lineas)
