import datetime
import logging
import re
import difflib
import unicodedata
from django.utils import timezone
from django.db.models import Q
from langchain_core.tools import tool

from core.models import Usuario, Turno, Reserva, Clase
from .profesores_tools import resolver_fecha, obtener_profesor_de_turno

logger = logging.getLogger(__name__)

# Almacén en memoria de las últimas coincidencias para Human-in-the-loop
_ULTIMAS_COINCIDENCIAS_ALUMNAS = []
_ULTIMA_ALUMNA_ACTIVA = None

def registrar_alumna_activa(alumna):
    global _ULTIMA_ALUMNA_ACTIVA
    if alumna:
        _ULTIMA_ALUMNA_ACTIVA = alumna

def get_ultima_alumna_activa():
    global _ULTIMA_ALUMNA_ACTIVA
    return _ULTIMA_ALUMNA_ACTIVA

def get_ultimas_coincidencias_alumnas():
    global _ULTIMAS_COINCIDENCIAS_ALUMNAS
    return list(_ULTIMAS_COINCIDENCIAS_ALUMNAS)

VERBOS_Y_STOPWORDS_GESTION = {
    'agregale', 'agregále', 'agrégale', 'agregarle', 'agrega', 'agregá', 'agregar',
    'sumale', 'súmale', 'sumarle', 'suma', 'sumá', 'sumar',
    'cargale', 'cárgale', 'cargarle', 'carga', 'cargá', 'cargar',
    'asignale', 'asígnale', 'asignarle', 'asigna', 'asigná', 'asignar',
    'renovale', 'renóvale', 'renovarle', 'renova', 'renová', 'renovar',
    'anotale', 'anótale', 'anotarle', 'anota', 'anotá', 'anotar',
    'agendale', 'agéndale', 'agendarle', 'agenda', 'agendá', 'agendar',
    'sacale', 'sácale', 'sacarle', 'saca', 'sacá', 'sacar',
    'desanota', 'desanotá', 'desanotale',
    'plan', 'planes', 'abono', 'abonos', 'clase', 'clases', 'credito', 'creditos', 'crédito', 'créditos',
    'su', 'sus', 'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'al', 'del', 'a', 'de', 'para', 'en', 'por', 'con',
    'hoy', 'mañana', 'sabado', 'sábado', 'lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes',
    'hs', 'horas'
}

def normalizar_texto_fonetico(texto: str) -> str:
    """Elimina acentos, diacríticos y reduce repeticiones para tolerar audios y ortografía"""
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto).lower())
    sin_tildes = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Reducir repetición de letras consecutivas (ej: marzzuck -> marzuk, laaaaila -> laila)
    sin_rep = re.sub(r'(.)\1+', r'\1', sin_tildes)
    return sin_rep.strip()

def formatear_opciones_human_in_the_loop(query: str, candidatas: list, accion_desc: str = "") -> str:
    """Genera una respuesta profesional con lista numerada para que Deby elija la alumna correcta"""
    lineas = [f"✦ Deby, encontré estas posibles coincidencias para '*{query}*':\n"]
    for idx, u in enumerate(candidatas, 1):
        tel_str = f" • Tel: ...{u.telefono[-4:]}" if u.telefono and len(u.telefono) >= 4 else ""
        abono_str = ""
        try:
            from plugins.membresias.backend.models import Suscripcion
            sub = Suscripcion.objects.filter(usuario=u, estado__in=['ACTIVO', 'AGOTADO']).first()
            if sub and sub.plan:
                abono_str = f" • Abono: {sub.plan.nombre} ({sub.clases_restantes} clases)"
        except Exception:
            pass
        lineas.append(f"{idx}. *{u.nombre} {u.apellido}*{tel_str}{abono_str}")
    
    accion_txt = f" para {accion_desc}" if accion_desc else ""
    lineas.append(f"\n¿Te referías a alguna de ellas? Podés indicarme el número (ej: *\"la 1\"*) o el nombre completo y continúo{accion_txt}.")
    return "\n".join(lineas)

def buscar_alumna_flexible(query: str):
    """
    Busca una alumna por nombre, apellido o teléfono de manera tolerante a mayúsculas, acentos
    y errores de tipeo o transcripción de audios (Fuzzy Matching).
    Retorna (alumna_encontrada, lista_coincidencias, error_str).
    """
    global _ULTIMAS_COINCIDENCIAS_ALUMNAS
    _ULTIMAS_COINCIDENCIAS_ALUMNAS = []

    q_clean = query.strip()
    if not q_clean:
        activa = get_ultima_alumna_activa()
        if activa:
            _ULTIMAS_COINCIDENCIAS_ALUMNAS = [activa]
            return activa, [activa], None
        return None, [], "No se especificó el nombre o teléfono de la alumna."

    # 1. Si es búsqueda por número de teléfono
    solo_num = re.sub(r'\D', '', q_clean)
    if len(solo_num) >= 6:
        ultimos = solo_num[-8:]
        qs = Usuario.objects.filter(telefono__icontains=ultimos)
        if qs.count() == 1:
            u = qs.first()
            registrar_alumna_activa(u)
            _ULTIMAS_COINCIDENCIAS_ALUMNAS = [u]
            return u, [u], None
        elif qs.count() > 1:
            _ULTIMAS_COINCIDENCIAS_ALUMNAS = list(qs)
            return None, list(qs), "multiples"

    # 2. Descartar verbos de orden, números y stopwords para aislar nombres propios
    tokens_reales = [
        p for p in re.findall(r'[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+', q_clean)
        if p.lower() not in VERBOS_Y_STOPWORDS_GESTION and len(p) >= 2
    ]

    # Si no hay tokens reales de nombre (ej: "Agrégale a su plan 4 clases", "su plan", "a su plan", "renovale")
    if not tokens_reales:
        activa = get_ultima_alumna_activa()
        if activa:
            logger.info(f"[ASISTENTE CONTEXTO] Usando alumna activa en contexto: {activa.nombre} {activa.apellido}")
            _ULTIMAS_COINCIDENCIAS_ALUMNAS = [activa]
            return activa, [activa], None
        return None, [], "No identifiqué a qué alumna te referís. ¿Me pasás su nombre o apellido?"

    # 3. Búsqueda exacta / subcadena en base de datos usando tokens limpios
    palabras = tokens_reales
    filtro = Q()
    for p in palabras:
        filtro |= Q(nombre__icontains=p) | Q(apellido__icontains=p) | Q(email__icontains=p)

    qs = list(Usuario.objects.filter(filtro).exclude(rol='PROFESOR').distinct())

    # Coincidencia directa
    if len(qs) == 1:
        u = qs[0]
        registrar_alumna_activa(u)
        _ULTIMAS_COINCIDENCIAS_ALUMNAS = [u]
        return u, [u], None
    elif len(qs) > 1:
        # Priorizar si una tiene el nombre completo exacto
        nombre_buscado_clean = " ".join(tokens_reales).lower()
        for u in qs:
            nom_comp = f"{u.nombre} {u.apellido}".lower()
            if nombre_buscado_clean == nom_comp or (nombre_buscado_clean in nom_comp and len(palabras) > 1):
                registrar_alumna_activa(u)
                _ULTIMAS_COINCIDENCIAS_ALUMNAS = [u]
                return u, [u], None
        _ULTIMAS_COINCIDENCIAS_ALUMNAS = qs
        return None, qs, "multiples"

    # 4. Fuzzy Matching fonético / ortográfico (difflib SequenceMatcher)
    # Especial para audios mal transcriptos o errores tipográficos (ej: 'marzuk' -> 'Marzzuck')
    q_norm = normalizar_texto_fonetico(" ".join(tokens_reales))
    todos_usuarios = list(Usuario.objects.exclude(rol='PROFESOR'))
    candidatos_con_score = []

    for u in todos_usuarios:
        nombre_u = u.nombre or ""
        apellido_u = u.apellido or ""
        full_u = f"{nombre_u} {apellido_u}".strip()
        
        fn = normalizar_texto_fonetico(full_u)
        an = normalizar_texto_fonetico(apellido_u)
        nn = normalizar_texto_fonetico(nombre_u)

        s_full = difflib.SequenceMatcher(None, q_norm, fn).ratio()
        s_ape = difflib.SequenceMatcher(None, q_norm, an).ratio()
        s_nom = difflib.SequenceMatcher(None, q_norm, nn).ratio()

        s_palabras = 0
        if len(palabras) > 1:
            for p in palabras:
                p_norm = normalizar_texto_fonetico(p)
                s_p = max(
                    difflib.SequenceMatcher(None, p_norm, an).ratio(),
                    difflib.SequenceMatcher(None, p_norm, nn).ratio()
                )
                if s_p > s_palabras:
                    s_palabras = s_p

        best_score = max(s_full, s_ape, s_nom, s_palabras)

        if best_score >= 0.58:
            candidatos_con_score.append((best_score, u))

    candidatos_con_score.sort(key=lambda x: x[0], reverse=True)

    if not candidatos_con_score:
        return None, [], f"No encontré ninguna alumna registrada con '{q_clean}' en el sistema."

    # Si hay un match con score muy alto (>= 0.88), tomarlo directo
    if candidatos_con_score[0][0] >= 0.88:
        u = candidatos_con_score[0][1]
        registrar_alumna_activa(u)
        _ULTIMAS_COINCIDENCIAS_ALUMNAS = [u]
        return u, [u], None

    # Al ser coincidencia difusa, devolvemos hasta 4 candidatas para Human-in-the-loop
    top_candidatos = [u for score, u in candidatos_con_score[:4]]
    _ULTIMAS_COINCIDENCIAS_ALUMNAS = top_candidatos
    return None, top_candidatos, "multiples"


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
        return formatear_opciones_human_in_the_loop(nombre_o_tel_alumna, matches, "renovarle el abono")
    elif not alumna:
        return f"✦ No encontré a ninguna alumna registrada como '{nombre_o_tel_alumna}' en Violett Pilates. Verificá cómo figura su nombre o pasame su número de teléfono."

    # Identificar cantidad de clases si vino pegada en el parámetro
    if not nombre_o_clases_plan:
        m_num = re.search(r'\b(1|4|8|12|16)\s*clases?\b', nombre_o_tel_alumna, re.IGNORECASE)
        if not m_num:
            m_num = re.search(r'\b(1|4|8|12|16)\b', nombre_o_tel_alumna)
        if m_num:
            nombre_o_clases_plan = m_num.group(1)

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
        return formatear_opciones_human_in_the_loop(nombre_o_tel, matches, "ver su ficha y abono")
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
    target_date = resolver_fecha(fecha_o_dia)
    hora_clean = hora_str.lower().replace('hs', '').replace('h', '').strip()
    if ':' not in hora_clean:
        try:
            hora_clean = f"{int(hora_clean):02d}:00"
        except ValueError:
            hora_clean = "18:00"

    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return formatear_opciones_human_in_the_loop(
            nombre_o_tel_alumna, 
            matches, 
            f"anotarla para el {target_date.strftime('%d/%m/%Y')} a las {hora_clean} hs"
        )

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
    if err == "multiples":
        return formatear_opciones_human_in_the_loop(
            nombre_o_tel_alumna,
            matches,
            f"darla de baja de la clase del {target_date.strftime('%d/%m/%Y')}" + (f" a las {hora_str}" if hora_str else "")
        )

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
def consultar_agenda_completa_dia(fecha_o_dia: str = "hoy", hora_str: str = "") -> str:
    """
    Comando para la dueña: muestra la grilla completa de clases del día con los nombres de las alumnas
    anotadas en cada camilla, profesoras a cargo y camillas vacías.
    Si se especifica 'hora_str' (ej: '18:00', '18hs', '15:30', '15'), detalla puntualmente quiénes asisten a esa clase.
    """
    target_date = resolver_fecha(fecha_o_dia)
    dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias_es[target_date.weekday()]

    turnos = Turno.objects.filter(
        fecha=target_date,
        estado='PROGRAMADO'
    ).prefetch_related('reservas__usuario').order_by('hora_inicio')

    if hora_str:
        h_clean = hora_str.lower().replace('hs', '').replace('h', '').strip()
        turnos = turnos.filter(hora_inicio__startswith=h_clean)

    if not turnos.exists():
        if hora_str:
            return f"✦ Deby, no encontré una clase programada a las {hora_str} para el {dia_nom} {target_date.strftime('%d/%m/%Y')}."
        return f"No hay turnos programados en la agenda para el {dia_nom} {target_date.strftime('%d/%m/%Y')}."

    if hora_str and turnos.count() == 1:
        t = turnos.first()
        prof_obj = obtener_profesor_de_turno(t)
        profe = f" | Profe: {prof_obj.nombre}" if prof_obj and hasattr(prof_obj, 'nombre') else ""
        reservas = [r for r in t.reservas.all() if r.estado == 'CONFIRMADA']
        cant = len(reservas)
        nombres = [(f"{r.usuario.nombre} {r.usuario.apellido}".strip() if r.usuario else (r.nombre_temporal or "Alumna puntual")) for r in reservas]
        nombres_str = ", ".join(nombres) if nombres else "Ninguna (todas las camillas libres)"
        libres = 3 - cant
        return f"✦ Clase de las {t.hora_inicio.strftime('%H:%M')} hs ({dia_nom} {target_date.strftime('%d/%m/%Y')}):\n• Alumnas inscriptas ({cant}/3): {nombres_str}\n• Camillas libres: {libres}\n• Profesora a cargo:{profe or ' Sin asignar'}"

    lineas = [f"✦ Agenda de Violett Pilates - {dia_nom} {target_date.strftime('%d/%m/%Y')}:"]
    for t in turnos:
        prof_obj = obtener_profesor_de_turno(t)
        profe = f" | Profe: {prof_obj.nombre}" if prof_obj and hasattr(prof_obj, 'nombre') else ""
        reservas = [r for r in t.reservas.all() if r.estado == 'CONFIRMADA']
        cant = len(reservas)
        nombres = [(f"{r.usuario.nombre} {r.usuario.apellido}".strip() if r.usuario else (r.nombre_temporal or "Alumna puntual")) for r in reservas]
        nombres_str = ", ".join(nombres) if nombres else "Sin alumnas aún"
        libres = 3 - cant
        lineas.append(f"• {t.hora_inicio.strftime('%H:%M')} hs ({cant}/3 ocupadas){profe}\n  Alumnas: {nombres_str} ({libres} camilla(s) libre(s))")

    return "\n\n".join(lineas)


@tool
def crear_clase_y_agendar_alumna_duena(fecha_o_dia: str, hora_str: str, nombre_o_tel_alumna: str = "") -> str:
    """
    Comando exclusivo de la dueña (Deby) para ABRIR o CREAR una clase/turno nuevo fuera de la grilla habitual
    en una fecha y horario puntual, y opcionalmente dejar anotada a una alumna en el mismo paso.
    Parámetros:
    - fecha_o_dia: Día de la semana o fecha (ej: 'sábado', 'mañana', 'hoy', '07/11/2026').
    - hora_str: Hora de inicio de la clase (ej: '17:00', '17hs', '17').
    - nombre_o_tel_alumna: Nombre o teléfono de la alumna a inscribir (ej: 'Alex Agüero', 'Martina'). Opcional.
    """
    target_date = resolver_fecha(fecha_o_dia)
    hora_clean = hora_str.lower().replace('hs', '').replace('h', '').strip()
    if ':' not in hora_clean:
        try:
            hora_clean = f"{int(hora_clean):02d}:00"
        except ValueError:
            hora_clean = "18:00"

    clase_obj = Clase.objects.filter(is_active=True).first()
    if not clase_obj:
        return "No hay una disciplina activa en el sistema para asociar la nueva clase."

    h, m = map(int, hora_clean.split(':'))
    h_fin = (h + 1) % 24

    turno = Turno.objects.filter(
        fecha=target_date,
        hora_inicio__startswith=hora_clean,
        estado='PROGRAMADO'
    ).first()

    es_nueva = False
    if not turno:
        turno = Turno.objects.create(
            clase=clase_obj,
            fecha=target_date,
            hora_inicio=datetime.time(h, m),
            hora_fin=datetime.time(h_fin, m),
            cupo_actual=clase_obj.cupo_maximo,
            estado='PROGRAMADO'
        )
        es_nueva = True

    dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias_es[target_date.weekday()]

    if not nombre_o_tel_alumna or not nombre_o_tel_alumna.strip():
        accion_str = "Creé la nueva clase" if es_nueva else "Ya existía la clase"
        return f"✦ ¡Listo Deby! {accion_str} de {clase_obj.nombre} para el {dia_nom} {target_date.strftime('%d/%m')} a las {hora_clean} hs ({turno.cupo_actual} camillas disponibles)."

    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return formatear_opciones_human_in_the_loop(
            nombre_o_tel_alumna,
            matches,
            f"anotarla para la clase del {dia_nom} {target_date.strftime('%d/%m')} a las {hora_clean} hs"
        )

    # Validar si ya está anotada
    if alumna:
        ya_anotada = Reserva.objects.filter(
            turno=turno,
            usuario=alumna,
            estado__in=['CONFIRMADA', 'TOMADA']
        ).exists()
        if ya_anotada:
            return f"✦ Deby, {alumna.nombre} {alumna.apellido} ya está inscripta en la clase del {dia_nom} {target_date.strftime('%d/%m')} a las {hora_clean} hs."

        if turno.cupo_actual <= 0:
            return f"✦ La clase del {dia_nom} {target_date.strftime('%d/%m')} a las {hora_clean} hs ya tiene todas sus camillas ocupadas."

        Reserva.objects.create(
            turno=turno,
            usuario=alumna,
            estado='CONFIRMADA'
        )
        turno.cupo_actual = max(0, turno.cupo_actual - 1)
        turno.save()

        # Descontar crédito de suscripción activa si tiene
        creditos_msg = ""
        try:
            from plugins.membresias.backend.models import Suscripcion
            sub = Suscripcion.objects.filter(usuario=alumna, estado='ACTIVO').order_by('-fecha_inicio').first()
            if sub and sub.clases_restantes > 0:
                sub.clases_restantes = max(0, sub.clases_restantes - 1)
                if sub.clases_restantes == 0:
                    sub.estado = 'AGOTADO'
                sub.save()
                creditos_msg = f" (Le quedan {sub.clases_restantes} clases en su {sub.plan.nombre})"
        except Exception:
            pass

        accion_str = "Creé la nueva clase" if es_nueva else "En la clase"
        return f"✦ ¡Listo Deby! {accion_str} de {clase_obj.nombre} para el {dia_nom} {target_date.strftime('%d/%m')} a las {hora_clean} hs y ya dejé anotado/a a {alumna.nombre} {alumna.apellido}{creditos_msg}. Quedan {turno.cupo_actual} camillas libres."
    else:
        # Reserva puntual manual sin cuenta
        if turno.cupo_actual <= 0:
            return f"✦ La clase del {dia_nom} {target_date.strftime('%d/%m')} a las {hora_clean} hs ya tiene todas sus camillas ocupadas."

        Reserva.objects.create(
            turno=turno,
            usuario=None,
            nombre_temporal=nombre_o_tel_alumna,
            estado='CONFIRMADA'
        )
        turno.cupo_actual = max(0, turno.cupo_actual - 1)
        turno.save()

        accion_str = "Creé la nueva clase" if es_nueva else "En la clase"
        return f"✦ ¡Listo Deby! {accion_str} para el {dia_nom} {target_date.strftime('%d/%m')} a las {hora_clean} hs y aparté una camilla a nombre de '{nombre_o_tel_alumna}'. Quedan {turno.cupo_actual} camillas libres."


@tool
def obtener_metricas_alumnas_duena(filtro: str = "") -> str:
    """
    Comando exclusivo para la dueña (Deby): informa la cantidad total de alumnas del estudio,
    cuántas tienen abono activo vigente, cuántas tienen el abono agotado, cuántas están inactivas
    y cuántas alumnas nuevas se registraron este mes.
    Parámetro:
    - filtro: Puede ser 'activas', 'agotadas', 'inactivas', 'nuevas' o vacío para el resumen completo.
    """
    today = timezone.localdate()
    total_alumnas = Usuario.objects.filter(rol='CLIENTE', is_active=True).count()

    try:
        from plugins.membresias.backend.models import Suscripcion
        subs_activas = Suscripcion.objects.filter(
            usuario__rol='CLIENTE',
            estado='ACTIVO',
            fecha_vencimiento__gte=today
        ).values('usuario').distinct().count()

        subs_agotadas = Suscripcion.objects.filter(
            usuario__rol='CLIENTE',
            estado='AGOTADO',
            fecha_vencimiento__gte=today
        ).values('usuario').distinct().count()
    except Exception:
        subs_activas = 0
        subs_agotadas = 0

    sin_abono = max(0, total_alumnas - subs_activas - subs_agotadas)

    nuevas_mes = Usuario.objects.filter(
        rol='CLIENTE',
        created_at__year=today.year,
        created_at__month=today.month
    ).count()

    return f"""✦ Estado Poblacional de Alumnas (Violett Pilates):
• Total de alumnas registradas: {total_alumnas}
• Con membresía activa vigente: {subs_activas} alumnas
• Con abono agotado (pendientes de renovar): {subs_agotadas} alumnas
• Sin abono activo o inactivas: {sin_abono} alumnas
• Nuevas alumnas sumadas este mes: {nuevas_mes}

¿Te gustaría que te pase la lista de alumnas para renovar o consultar la ficha de alguna en particular?"""


@tool
def ajustar_creditos_alumna_duena(nombre_o_tel_alumna: str, cantidad_creditos: int = 1, motivo: str = "Ajuste manual de la dueña") -> str:
    """
    Comando exclusivo para la dueña (Deby): suma o resta clases individuales al abono de una alumna puntual
    (ej: para regalarle una clase de cortesía, compensación, o descontar una clase).
    Parámetros:
    - nombre_o_tel_alumna: Nombre, apellido o teléfono de la alumna.
    - cantidad_creditos: Número positivo para sumar clases (ej: 1, 2) o negativo para restar (ej: -1).
    - motivo: Razón del ajuste (opcional).
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        accion_desc = f"sumarle {cantidad_creditos} clase(s)" if cantidad_creditos > 0 else f"restarle {abs(cantidad_creditos)} clase(s)"
        return formatear_opciones_human_in_the_loop(nombre_o_tel_alumna, matches, accion_desc)
    elif not alumna:
        return f"✦ No encontré a ninguna alumna registrada con '{nombre_o_tel_alumna}' en Violett Pilates."

    try:
        from plugins.membresias.backend.models import Suscripcion
        sub = Suscripcion.objects.filter(usuario=alumna, estado__in=['ACTIVO', 'AGOTADO']).order_by('-fecha_inicio').first()
        if not sub:
            return f"✦ {alumna.nombre} {alumna.apellido} no tiene ningún abono activo en este momento para ajustarle clases."

        sub.clases_restantes = max(0, sub.clases_restantes + cantidad_creditos)
        if sub.clases_restantes > 0 and sub.estado == 'AGOTADO':
            sub.estado = 'ACTIVO'
        sub.save()

        nombre_completo = f"{alumna.nombre} {alumna.apellido}".strip()
        operacion = f"sumé {cantidad_creditos}" if cantidad_creditos > 0 else f"resté {abs(cantidad_creditos)}"
        return f"✦ ¡Listo Deby! Le {operacion} clase(s) a {nombre_completo}. Ahora tiene {sub.clases_restantes} clase(s) disponibles en su {sub.plan.nombre} (Vence el {sub.fecha_vencimiento.strftime('%d/%m/%Y')})."
    except Exception as e:
        return f"✦ Ocurrió un error al actualizar los créditos: {e}"


@tool
def consultar_esquema_fijo_alumna(nombre_o_tel_alumna: str) -> str:
    """
    Comando para la dueña: consulta qué días y horarios fijos semanales tiene asignados una alumna en la grilla.
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return formatear_opciones_human_in_the_loop(nombre_o_tel_alumna, matches, "ver su esquema fijo")
    elif not alumna:
        return f"✦ No encontré a ninguna alumna registrada como '{nombre_o_tel_alumna}' en Violett Pilates."

    try:
        from plugins.recurrencias.backend.models import Recurrencia
        recs = Recurrencia.objects.filter(usuario=alumna, is_active=True).select_related('clase').order_by('dia_semana', 'hora_inicio')
    except Exception:
        recs = []

    nombre_comp = f"{alumna.nombre} {alumna.apellido}".strip()
    if not recs:
        return f"✦ {nombre_comp} no tiene ningún horario fijo semanal asignado en este momento."

    dias_nombres = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
    lineas = [f"✦ Esquema Fijo Semanal: {nombre_comp}"]
    for r in recs:
        dia_txt = dias_nombres.get(r.dia_semana, f'Día {r.dia_semana}')
        hora_txt = r.hora_inicio.strftime('%H:%M')
        lineas.append(f"  • {dia_txt} a las {hora_txt} hs ({r.clase.nombre})")

    return "\n".join(lineas)


@tool
def asignar_horario_fijo_alumna(nombre_o_tel_alumna: str, dia_semana_str: str, hora_str: str) -> str:
    """
    Comando para la dueña: asigna un horario fijo semanal a una alumna en la grilla
    (ej: 'poner fija a Alex los sábados a las 11hs', 'horario fijo para Marcela martes 18hs').
    Parámetros:
    - nombre_o_tel_alumna: Nombre de la alumna.
    - dia_semana_str: 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'.
    - hora_str: Hora de inicio (ej: '11:00', '18', '19:30').
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return formatear_opciones_human_in_the_loop(nombre_o_tel_alumna, matches, f"asignarle horario fijo {dia_semana_str} {hora_str}")
    elif not alumna:
        return f"✦ No encontré a ninguna alumna registrada como '{nombre_o_tel_alumna}' en Violett Pilates."

    dias_map = {
        'lunes': 1, 'martes': 2, 'miercoles': 3, 'miércoles': 3,
        'jueves': 4, 'viernes': 5, 'sabado': 6, 'sábado': 6, 'domingo': 7
    }
    dia_num = 1
    for d_nombre, d_val in dias_map.items():
        if d_nombre in dia_semana_str.lower():
            dia_num = d_val
            break

    hora_clean = hora_str.lower().replace('hs', '').replace('h', '').strip()
    if ':' not in hora_clean:
        try:
            h_int = int(re.search(r'\d+', hora_clean).group(0))
            hora_clean = f"{h_int:02d}:00"
        except Exception:
            hora_clean = "18:00"

    try:
        from core.models import Clase
        from plugins.recurrencias.backend.models import Recurrencia
        from plugins.membresias.backend.models import Suscripcion
        from plugins.recurrencias.backend.services import auto_agendar_recurrencias_usuario

        clase_reformer = Clase.objects.filter(is_active=True).first()
        if not clase_reformer:
            return "No hay clases activas en el sistema para asociar la recurrencia."

        rec, created = Recurrencia.objects.get_or_create(
            usuario=alumna,
            clase=clase_reformer,
            dia_semana=dia_num,
            hora_inicio=hora_clean,
            defaults={'is_active': True}
        )
        if not created and not rec.is_active:
            rec.is_active = True
            rec.save(update_fields=['is_active'])

        dias_nombres = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
        dia_display = dias_nombres.get(dia_num, dia_semana_str)
        nombre_comp = f"{alumna.nombre} {alumna.apellido}".strip()

        sub = Suscripcion.objects.filter(usuario=alumna, estado='ACTIVO').order_by('-fecha_inicio').first()
        agendadas = 0
        if sub:
            agendadas = auto_agendar_recurrencias_usuario(alumna, sub)

        msg_extra = f" Además, agendé automáticamente {agendadas} clase(s) en sus turnos próximos." if agendadas > 0 else ""
        return f"✦ ¡Listo Deby! ✦ Le asigné a {nombre_comp} el horario fijo semanal de los *{dia_display} a las {hora_clean} hs*.{msg_extra}"
    except Exception as e:
        return f"✦ Ocurrió un error al guardar el horario fijo: {e}"


@tool
def dar_baja_horario_fijo_alumna(nombre_o_tel_alumna: str, dia_semana_str: str = "", hora_str: str = "") -> str:
    """
    Comando para la dueña: desactiva los horarios fijos semanales de una alumna
    (ej: 'sacale el horario fijo a Alex', 'dar de baja la recurrencia de Marcela').
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return formatear_opciones_human_in_the_loop(nombre_o_tel_alumna, matches, "desactivar su horario fijo")
    elif not alumna:
        return f"✦ No encontré a ninguna alumna registrada como '{nombre_o_tel_alumna}' en Violett Pilates."

    try:
        from plugins.recurrencias.backend.models import Recurrencia
        qs = Recurrencia.objects.filter(usuario=alumna, is_active=True)
        cant = qs.count()
        if cant == 0:
            return f"✦ {alumna.nombre} {alumna.apellido} no tiene ningún horario fijo semanal activo."

        qs.update(is_active=False)
        return f"✦ ¡Listo Deby! Desactivé los {cant} horario(s) fijo(s) de {alumna.nombre} {alumna.apellido}."
    except Exception as e:
        return f"✦ Error desactivando horario fijo: {e}"


@tool
def apartar_camilla_duena(fecha_o_dia: str, hora_str: str, motivo: str = "Reserva de dirección / Mantenimiento") -> str:
    """
    Comando para la dueña: bloquea o aparta una camilla puntual en un turno específico para que ninguna alumna la pueda reservar
    (ej: 'apartá una camilla mañana a las 18hs', 'bloqueá una camilla el sábado a las 11hs por mantenimiento').
    """
    target_date = resolver_fecha(fecha_o_dia)
    hora_clean = hora_str.lower().replace('hs', '').replace('h', '').strip()
    if ':' not in hora_clean:
        try:
            h_int = int(re.search(r'\d+', hora_clean).group(0))
            hora_clean = f"{h_int:02d}:00"
        except Exception:
            hora_clean = "18:00"

    t = Turno.objects.filter(fecha=target_date, hora_inicio__startswith=hora_clean[:2]).first()
    if not t:
        return f"✦ No encontré un turno programado a las {hora_str} para el {target_date.strftime('%d/%m/%Y')}."

    if t.cupo_actual <= 0:
        return f"✦ En ese turno ya no quedan camillas disponibles para bloquear (ocupación al 100%)."

    try:
        from core.models import Reserva
        Reserva.objects.create(
            turno=t,
            tipo_reserva='BLOQUEO',
            nombre_temporal=motivo,
            estado='CONFIRMADA'
        )
        t.cupo_actual = max(0, t.cupo_actual - 1)
        t.save()
        return f"✦ ¡Listo Deby! ✦ Aparté 1 camilla en el turno del {target_date.strftime('%d/%m/%Y')} a las {t.hora_inicio.strftime('%H:%M')} hs (Motivo: *{motivo}*). Quedan {t.cupo_actual} camilla(s) libre(s) para alumnas."
    except Exception as e:
        return f"✦ Error al bloquear la camilla: {e}"


@tool
def liberar_camilla_bloqueada_duena(fecha_o_dia: str, hora_str: str) -> str:
    """
    Comando para la dueña: desbloquea una camilla apartada previamente en un turno, devolviéndola al cupo disponible.
    """
    target_date = resolver_fecha(fecha_o_dia)
    hora_clean = hora_str.lower().replace('hs', '').replace('h', '').strip()
    if ':' not in hora_clean:
        try:
            h_int = int(re.search(r'\d+', hora_clean).group(0))
            hora_clean = f"{h_int:02d}:00"
        except Exception:
            hora_clean = "18:00"

    t = Turno.objects.filter(fecha=target_date, hora_inicio__startswith=hora_clean[:2]).first()
    if not t:
        return f"✦ No encontré el turno de las {hora_str} para el {target_date.strftime('%d/%m/%Y')}."

    try:
        from core.models import Reserva
        res_bloqueo = Reserva.objects.filter(turno=t, tipo_reserva='BLOQUEO', estado='CONFIRMADA').first()
        if not res_bloqueo:
            return f"✦ No hay ninguna camilla bloqueada en ese turno."

        res_bloqueo.estado = 'CANCELADA'
        res_bloqueo.save()
        t.cupo_actual += 1
        t.save()
        return f"✦ ¡Listo Deby! Liberé la camilla bloqueada. Ahora hay {t.cupo_actual} camilla(s) disponible(s) en ese horario."
    except Exception as e:
        return f"✦ Error al liberar la camilla: {e}"


@tool
def dar_baja_plan_alumna_duena(nombre_o_tel_alumna: str) -> str:
    """
    Comando para la dueña: da de baja definitivamente el plan activo de una alumna y cancela sus turnos futuros agendados
    (ej: 'dar de baja el plan de Alex', 'cancelale el abono a Marcela').
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return formatear_opciones_human_in_the_loop(nombre_o_tel_alumna, matches, "dar de baja su plan")
    elif not alumna:
        return f"✦ No encontré a ninguna alumna registrada como '{nombre_o_tel_alumna}' en Violett Pilates."

    try:
        from plugins.membresias.backend.models import Suscripcion
        from core.models import Reserva
        today = timezone.localdate()

        subs = Suscripcion.objects.filter(usuario=alumna, estado__in=['ACTIVO', 'AGOTADO'])
        if not subs.exists():
            return f"✦ {alumna.nombre} {alumna.apellido} no tiene ningún abono activo para dar de baja."

        subs.update(estado='VENCIDO', clases_restantes=0)

        futuras = Reserva.objects.filter(usuario=alumna, turno__fecha__gte=today, estado='CONFIRMADA')
        cant_turnos = futuras.count()
        for r in futuras:
            r.estado = 'CANCELADA'
            r.save()
            t = r.turno
            t.cupo_actual += 1
            t.save()

        nombre_comp = f"{alumna.nombre} {alumna.apellido}".strip()
        msg_turnos = f" y se liberaron {cant_turnos} clase(s) agendadas a futuro" if cant_turnos > 0 else ""
        return f"✦ ¡Listo Deby! ✦ Di de baja el abono de {nombre_comp}{msg_turnos}. Su ficha quedó sin abono activo."
    except Exception as e:
        return f"✦ Error al dar de baja el plan: {e}"


@tool
def consultar_ultimas_resenas_duena() -> str:
    """
    Comando para la dueña: consulta las últimas opiniones, calificaciones de estrellas y testimonios dejados por las alumnas en la web.
    """
    try:
        from plugins.resenas.backend.models import Resena
        from django.db.models import Avg
        resenas = Resena.objects.select_related('usuario').order_by('-fecha')[:5]
        if not resenas.exists():
            return "✦ Por el momento no se han registrado reseñas de alumnas en la plataforma web."

        total_resenas = Resena.objects.count()
        promedio = Resena.objects.aggregate(Avg('estrellas'))['estrellas__avg'] or 5.0

        lineas = [
            f"✦ Opiniones y Reseñas de Alumnas (Violett Pilates):",
            f"• Promedio general: {promedio:.1f} / 5.0 ★ (de {total_resenas} opiniones)",
            f"\nÚltimos testimonios recibidos:"
        ]

        for r in resenas:
            u_nom = f"{r.usuario.nombre} {r.usuario.apellido}".strip() if r.usuario else "Alumna"
            estrellas_str = "★" * r.estrellas + "☆" * (5 - r.estrellas)
            fecha_str = r.fecha.strftime('%d/%m/%Y') if hasattr(r, 'fecha') and r.fecha else ""
            txt = f"_{r.mensaje}_" if r.mensaje else "Sin comentario escrito"
            lineas.append(f"• *{u_nom}* ({estrellas_str}) - {fecha_str}\n  {txt}")

        return "\n".join(lineas)
    except Exception as e:
        return f"✦ Ocurrió un error al consultar las reseñas: {e}"
