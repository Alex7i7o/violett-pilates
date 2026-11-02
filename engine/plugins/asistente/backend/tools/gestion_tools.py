import datetime
import logging
import re
from django.utils import timezone
from django.db.models import Q
from langchain_core.tools import tool

from core.models import Usuario, Turno, Reserva
from .profesores_tools import resolver_fecha, obtener_profesor_de_turno

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

    # 3. Disparar hooks de eventos
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
    ).select_related('turno', 'turno__clase').order_by('turno__fecha', 'turno__hora_inicio')[:5]

    if futuras.exists():
        dias_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        lista_turnos = []
        for r in futuras:
            t = r.turno
            dia_str = dias_es[t.fecha.weekday()]
            prof_obj = obtener_profesor_de_turno(t)
            profe = f" (Profe: {prof_obj.nombre})" if prof_obj and hasattr(prof_obj, 'nombre') else ""
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
    - nombre_o_tel_alumna: Nombre o teléfono de la alumna (ej: 'Laila Marzzuck', 'Alejandra Rivarola').
    - fecha_o_dia: 'hoy', 'mañana' o nombre del día (ej: 'lunes', 'martes', 'miércoles', 'jueves', 'viernes').
    - hora_str: Hora de inicio (ej: '15:30', '18:00', '19', '20').
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return f"Encontré varias alumnas con ese nombre. Por favor especificá el apellido completo o teléfono."

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
    ).select_related('clase')

    if not turnos.exists():
        # Si la hora exacta no existe, buscar los turnos disponibles de ese día para sugerirlos
        turnos_dia = Turno.objects.filter(fecha=target_date, estado='PROGRAMADO', cupo_actual__gt=0).select_related('clase').order_by('hora_inicio')
        if turnos_dia.exists():
            lista_horarios = []
            for t_item in turnos_dia:
                p_item = obtener_profesor_de_turno(t_item)
                p_str = f" (Profe: {p_item.nombre})" if p_item and hasattr(p_item, 'nombre') else ""
                lista_horarios.append(f"• {t_item.hora_inicio.strftime('%H:%M')} hs: {t_item.cupo_actual} camilla(s) libre(s){p_str}")
            return f"✦ No encontré una clase programada exactamente a las {hora_clean} hs para el {target_date.strftime('%d/%m/%Y')}.\n\nLos horarios con camillas disponibles para ese día son:\n" + "\n".join(lista_horarios) + f"\n\n¿En cuál de estos querés que anote a {nombre_o_tel_alumna}?"
        else:
            return f"✦ No encontré ninguna clase programada para el {target_date.strftime('%d/%m/%Y')} a las {hora_clean} hs, y para esa fecha todas las camillas están completas o no hay grilla."

    turno = turnos.first()

    # Si la alumna no está registrada en el sistema, la anotamos como reserva puntual/manual
    if not alumna:
        if turno.cupo_actual <= 0:
            return f"La clase del {target_date.strftime('%d/%m')} a las {hora_clean} hs ya tiene todas sus camillas ocupadas."
        reserva = Reserva.objects.create(
            turno=turno,
            usuario=None,
            nombre_temporal=nombre_o_tel_alumna.strip(),
            tipo_reserva='MANUAL_TEMPORAL',
            es_recurrente=False,
            estado='CONFIRMADA'
        )
        turno.cupo_actual = max(0, turno.cupo_actual - 1)
        turno.save()
        prof_obj = obtener_profesor_de_turno(turno)
        profe_str = f" con la profe {prof_obj.nombre}" if prof_obj and hasattr(prof_obj, 'nombre') else ""
        return f"✦ ¡Listo Deby! Anoté a {nombre_o_tel_alumna.strip()} para el {target_date.strftime('%d/%m/%Y')} a las {turno.hora_inicio.strftime('%H:%M')} hs{profe_str} (como alumna invitada). Quedan {turno.cupo_actual} camilla(s) libre(s) en ese bloque."

    # Verificar si ya está anotada
    if Reserva.objects.filter(turno=turno, usuario=alumna, estado='CONFIRMADA').exists():
        return f"{alumna.nombre} ya tiene una camilla reservada en ese horario ({target_date.strftime('%d/%m')} a las {hora_clean} hs)."

    if turno.cupo_actual <= 0:
        return f"La clase del {target_date.strftime('%d/%m')} a las {hora_clean} hs ya tiene todas sus camillas ocupadas."

    # Verificar membresía
    from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
    sub = Suscripcion.objects.filter(usuario=alumna, estado__in=['ACTIVO', 'AGOTADO']).first()

    reserva = Reserva.objects.create(
        turno=turno,
        usuario=alumna,
        estado='CONFIRMADA'
    )
    turno.cupo_actual = max(0, turno.cupo_actual - 1)
    turno.save()

    if sub:
        ReservaMembresia.objects.create(reserva=reserva, suscripcion=sub)
        if sub.clases_restantes > 0:
            sub.clases_restantes -= 1
            if sub.clases_restantes == 0:
                sub.estado = 'AGOTADO'
            sub.save()

    nombre_completo = f"{alumna.nombre} {alumna.apellido}".strip()
    prof_obj = obtener_profesor_de_turno(turno)
    profe_str = f" con la profe {prof_obj.nombre}" if prof_obj and hasattr(prof_obj, 'nombre') else ""
    return f"✦ ¡Listo Deby! Anoté a {nombre_completo} para el {target_date.strftime('%d/%m/%Y')} a las {turno.hora_inicio.strftime('%H:%M')} hs{profe_str}. Quedan {turno.cupo_actual} camilla(s) libre(s) en ese bloque."


@tool
def cancelar_reserva_alumna_duena(nombre_o_tel_alumna: str, fecha_o_dia: str = "hoy", hora_str: str = "") -> str:
    """
    Comando para la dueña: cancela la reserva de una alumna en una clase puntual y libera la camilla (sacar alumna de la clase).
    """
    target_date = resolver_fecha(fecha_o_dia)
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)

    qs = Reserva.objects.filter(turno__fecha=target_date, estado='CONFIRMADA').select_related('turno', 'usuario')

    if alumna:
        qs = qs.filter(usuario=alumna)
    else:
        # Si no existe como usuario, buscar por nombre temporal (alumna manual)
        qs = qs.filter(nombre_temporal__icontains=nombre_o_tel_alumna.strip())

    if hora_str:
        h = hora_str.lower().replace('hs', '').replace('h', '').strip()
        qs = qs.filter(turno__hora_inicio__startswith=h)

    if not qs.exists():
        nom_ref = alumna.nombre if alumna else nombre_o_tel_alumna
        return f"✦ No encontré ninguna reserva activa de {nom_ref} para el {target_date.strftime('%d/%m/%Y')}."

    reserva = qs.first()
    turno = reserva.turno
    reserva.estado = 'CANCELADA_TIEMPO'
    reserva.save()

    max_c = turno.clase.cupo_maximo if turno.clase else 3
    turno.cupo_actual = min(max_c, turno.cupo_actual + 1)
    turno.save()

    # Reintegrar crédito si es alumna registrada
    if reserva.usuario:
        from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
        ReservaMembresia.objects.filter(reserva=reserva).delete()
        sub = Suscripcion.objects.filter(usuario=reserva.usuario, estado__in=['ACTIVO', 'AGOTADO']).first()
        if sub:
            sub.clases_restantes += 1
            sub.estado = 'ACTIVO'
            sub.save()

    from backend_core.hooks import registry
    try:
        registry.execute('reserva_cancelada_a_tiempo', reserva)
    except Exception:
        pass

    nombre_display = f"{reserva.usuario.nombre} {reserva.usuario.apellido}".strip() if reserva.usuario else (reserva.nombre_temporal or nombre_o_tel_alumna)
    return f"✦ ¡Listo Deby! Saqué a {nombre_display} de la clase del {target_date.strftime('%d/%m/%Y')} a las {turno.hora_inicio.strftime('%H:%M')} hs. Se liberó la camilla (ahora hay {turno.cupo_actual} libres) y se le reintegró el crédito en su abono."


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
    ).prefetch_related('reservas__usuario').order_by('hora_inicio')

    if not turnos.exists():
        return f"No hay turnos programados en la agenda para el {dia_nom} {target_date.strftime('%d/%m/%Y')}."

    lineas = [f"✦ Agenda de Violett Pilates - {dia_nom} {target_date.strftime('%d/%m/%Y')}:"]
    for t in turnos:
        prof_obj = obtener_profesor_de_turno(t)
        profe = f" | Profe: {prof_obj.nombre}" if prof_obj and hasattr(prof_obj, 'nombre') else ""
        reservas = [r for r in t.reservas.all() if r.estado == 'CONFIRMADA']
        cant = len(reservas)
        nombres = [f"{r.usuario.nombre} {r.usuario.apellido}".strip() for r in reservas]
        nombres_str = ", ".join(nombres) if nombres else "Sin alumnas aún"
        libres = 3 - cant
        lineas.append(f"• {t.hora_inicio.strftime('%H:%M')} hs ({cant}/3 ocupadas){profe}\n  Alumnas: {nombres_str} ({libres} camilla(s) libre(s))")

    return "\n\n".join(lineas)
