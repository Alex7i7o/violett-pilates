import datetime
import logging
import re
import difflib
import unicodedata
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from langchain_core.tools import tool

from core.models import Usuario, Turno, Reserva, Clase
from .profesores_tools import resolver_fecha, resolver_hora, obtener_profesor_de_turno

logger = logging.getLogger(__name__)

# Almacén en memoria y sesión de las últimas coincidencias para Human-in-the-loop y contexto
_ULTIMAS_COINCIDENCIAS_ALUMNAS = []
_ULTIMA_ALUMNA_ACTIVA = None
_CONVERSACION_ACTIVA = None

def set_conversacion_activa(conversacion):
    """Sincroniza la conversación actual y restaura la alumna activa desde su metadata en BD"""
    global _CONVERSACION_ACTIVA, _ULTIMA_ALUMNA_ACTIVA
    _CONVERSACION_ACTIVA = conversacion
    if conversacion and getattr(conversacion, 'metadata', None):
        alumna_meta = conversacion.metadata.get('alumna_activa')
        if alumna_meta and isinstance(alumna_meta, dict):
            u_id = alumna_meta.get('id')
            if u_id:
                try:
                    from core.models import Usuario
                    u = Usuario.objects.filter(id=u_id).first()
                    if u:
                        _ULTIMA_ALUMNA_ACTIVA = u
                except Exception:
                    pass

def registrar_alumna_activa(alumna):
    global _ULTIMA_ALUMNA_ACTIVA, _CONVERSACION_ACTIVA
    if alumna:
        _ULTIMA_ALUMNA_ACTIVA = alumna
        if _CONVERSACION_ACTIVA and hasattr(_CONVERSACION_ACTIVA, 'metadata'):
            try:
                nom = f"{alumna.nombre} {alumna.apellido}".strip()
                if not isinstance(_CONVERSACION_ACTIVA.metadata, dict):
                    _CONVERSACION_ACTIVA.metadata = {}
                _CONVERSACION_ACTIVA.metadata['alumna_activa'] = {
                    'id': str(alumna.id),
                    'nombre': nom
                }
                _CONVERSACION_ACTIVA.save(update_fields=['metadata'])
            except Exception as e:
                logger.warning(f"No se pudo persistir alumna_activa en metadata: {e}")

def get_ultima_alumna_activa():
    global _ULTIMA_ALUMNA_ACTIVA
    return _ULTIMA_ALUMNA_ACTIVA

def get_ultimas_coincidencias_alumnas():
    global _ULTIMAS_COINCIDENCIAS_ALUMNAS
    return list(_ULTIMAS_COINCIDENCIAS_ALUMNAS)

def get_conversacion_activa():
    global _CONVERSACION_ACTIVA
    return _CONVERSACION_ACTIVA

def buscar_usuario_por_telefono(phone_str: str):
    """
    Busca un usuario por número de teléfono de forma tolerante a formatos
    (con o sin código de país 549, 11, espacios, guiones o prefijos locales).
    """
    if not phone_str:
        return None
    try:
        from core.models import Usuario
        clean_digits = re.sub(r'\D', '', str(phone_str))
        if not clean_digits:
            return None

        # 1. Búsqueda exacta
        u = Usuario.objects.filter(telefono__iexact=str(phone_str).strip()).first()
        if u:
            return u
        u = Usuario.objects.filter(telefono__iexact=clean_digits).first()
        if u:
            return u

        # 2. Búsqueda por últimos 8 dígitos
        if len(clean_digits) >= 8:
            u8 = clean_digits[-8:]
            u = Usuario.objects.filter(telefono__icontains=u8).first()
            if u:
                return u

        # 3. Comparación dígito a dígito con todos los usuarios
        for cand in Usuario.objects.exclude(telefono__isnull=True).exclude(telefono=''):
            c_digits = re.sub(r'\D', '', cand.telefono)
            if not c_digits or len(c_digits) < 6:
                continue
            if c_digits == clean_digits:
                return cand
            if clean_digits.endswith(c_digits) or cand_digits.endswith(clean_digits):
                return cand
            if len(c_digits) >= 7 and len(clean_digits) >= 7 and c_digits[-7:] == clean_digits[-7:]:
                return cand
    except Exception as e:
        logger.warning(f"Error en buscar_usuario_por_telefono: {e}")
    return None

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
    'ponele', 'ponéle', 'pónele', 'pone', 'poné', 'poner', 'ponerle',
    'dale', 'darle', 'dame',
    'mas', 'más', 'que', 'q',
    'plan', 'planes', 'abono', 'abonos', 'clase', 'clases', 'credito', 'creditos', 'crédito', 'créditos',
    'su', 'sus', 'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'al', 'del', 'a', 'de', 'para', 'en', 'por', 'con',
    'hoy', 'mañana', 'sabado', 'sábado', 'lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes',
    'hs', 'horas'
}


def normalizar_hora_str(hora_str: str, texto_completo: str = "") -> str:
    """
    Normaliza expresiones como '5', 'a las 5', '5 de la tarde', '17', '17hs', '17:00' a '17:00'.
    Mantiene compatibilidad con horarios matutinos (08:00, 09:00, 10:00, 11:00) y vespertinos (15:00..21:00).
    """
    texto = (str(hora_str) + " " + str(texto_completo)).lower()
    
    # 1. Formato explícito HH:MM
    m_hhmm = re.search(r'\b([01]?\d|2[0-3]):([0-5]\d)\b', hora_str)
    if m_hhmm:
        h = int(m_hhmm.group(1))
        m = int(m_hhmm.group(2))
        return f"{h:02d}:{m:02d}"

    # 2. Extraer número
    m_num = re.search(r'\b(\d{1,2})\b', hora_str)
    if not m_num:
        m_num = re.search(r'\b(?:a\s+las?|las?)\s*(\d{1,2})\b', texto)

    if m_num:
        val = int(m_num.group(1))
        es_tarde = any(k in texto for k in ['tarde', 'pm', 'p.m.', 'noche'])
        if (es_tarde or val in [1, 2, 3, 4, 5, 6, 7]) and val <= 12:
            val += 12
        return f"{val:02d}:00"

    return "18:00"

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
    # Priorizar perfiles que tienen teléfono válido y están activos (evita perfiles duplicados o fantasmas sin contacto)
    qs.sort(key=lambda x: (
        1 if (getattr(x, 'telefono', None) and len(re.sub(r'\D', '', str(x.telefono))) >= 6) else 0,
        1 if getattr(x, 'is_active', True) else 0
    ), reverse=True)

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

        # Prioridad de contexto inmediato: si entre las candidatas está la alumna activa, seleccionarla directamente
        activa = get_ultima_alumna_activa()
        if activa and any(u.id == activa.id for u in qs):
            for u in qs:
                if u.id == activa.id:
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
    activa = get_ultima_alumna_activa()
    if activa and any(u.id == activa.id for u in top_candidatos):
        for u in top_candidatos:
            if u.id == activa.id:
                registrar_alumna_activa(u)
                _ULTIMAS_COINCIDENCIAS_ALUMNAS = [u]
                return u, [u], None
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

    from backend_core.hooks import registry
    try:
        registry.execute('reserva_creada', reserva)
    except Exception as ex_h:
        logger.warning(f"Error hook reserva_creada en agendar_alumna_en_turno_duena: {ex_h}")

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

        res_creada = Reserva.objects.create(
            turno=turno,
            usuario=alumna,
            estado='CONFIRMADA'
        )
        turno.cupo_actual = max(0, turno.cupo_actual - 1)
        turno.save()
        from backend_core.hooks import registry
        try:
            registry.execute('reserva_creada', res_creada)
        except Exception as ex_h:
            logger.warning(f"Error hook reserva_creada: {ex_h}")

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
        if sub.fecha_vencimiento and sub.fecha_vencimiento < timezone.localdate():
            sub.fecha_vencimiento = timezone.localdate() + datetime.timedelta(days=30)
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

    hora_clean = normalizar_hora_str(hora_str, dia_semana_str)

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

        # Asegurar que la clase exista en el Esquema Semanal (PlantillaTurno) para que la web lo muestre y genere turnos
        from core.models import PlantillaTurno
        from core.services import generar_turnos_desde_plantillas
        h_i, m_i = map(int, hora_clean.split(':'))
        h_f = (h_i + 1) % 24
        t_inicio = datetime.time(h_i, m_i)
        t_fin = datetime.time(h_f, m_i)
        plantilla, p_created = PlantillaTurno.objects.get_or_create(
            clase=clase_reformer,
            dia_semana=dia_num,
            hora_inicio=t_inicio,
            defaults={'hora_fin': t_fin, 'is_active': True}
        )
        if not p_created and not plantilla.is_active:
            plantilla.is_active = True
            plantilla.save(update_fields=['is_active'])

        generar_turnos_desde_plantillas()

        dias_nombres = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
        dia_display = dias_nombres.get(dia_num, dia_semana_str)
        nombre_comp = f"{alumna.nombre} {alumna.apellido}".strip()

        sub = Suscripcion.objects.filter(usuario=alumna, estado='ACTIVO').order_by('-fecha_inicio').first()
        agendadas = 0
        if sub:
            agendadas = auto_agendar_recurrencias_usuario(alumna, sub)

        msg_extra = f" Además, agendé automáticamente {agendadas} clase(s) en sus turnos próximos." if agendadas > 0 else ""
        try:
            from plugins.comunicaciones.backend.whatsapp_service import notificar_horario_fijo_alumna
            notificar_horario_fijo_alumna(alumna, dia_num, hora_clean, "Pilates Reformer", "", "asignado")
        except Exception as ex_notif:
            logger.warning(f"Error notificando horario fijo a alumna: {ex_notif}")
        return f"✦ ¡Listo Deby! ✦ Le asigné a {nombre_comp} el horario fijo semanal de los *{dia_display} a las {hora_clean} hs*.{msg_extra} Le enviamos la confirmación por WhatsApp 🌸."
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
        try:
            from plugins.comunicaciones.backend.whatsapp_service import notificar_horario_fijo_alumna
            notificar_horario_fijo_alumna(alumna, 1, "fijo", "Pilates Reformer", "", "dada_de_baja")
        except Exception as ex_notif:
            logger.warning(f"Error notificando baja horario fijo: {ex_notif}")
        return f"✦ ¡Listo Deby! Desactivé los {cant} horario(s) fijo(s) de {alumna.nombre} {alumna.apellido} y le avisamos por WhatsApp."
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

        res_bloqueo.estado = 'CANCELADA_TIEMPO'
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
            r.estado = 'CANCELADA_TIEMPO'
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


@tool
def agregar_horario_esquema_semanal_duena(dia_semana_str: str, hora_str: str, nombre_profesora: str = "", nombre_o_tel_alumna: str = "") -> str:
    """
    Comando exclusivo de la dueña (Deby) para agregar un horario fijo al ESQUEMA SEMANAL (esqueleto del negocio).
    Crea la plantilla recurrente para que todos los días de esa semana (ej: todos los sábados del mes) se generen automáticamente
    con sus camillas libres en la Agenda web, asigna la profesora a cargo, y opcionalmente inscribe de forma fija a una alumna.
    Parámetros:
    - dia_semana_str: Día de la semana (ej: 'sábado', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes').
    - hora_str: Hora de inicio (ej: '17:00', '17hs', '5 de la tarde').
    - nombre_profesora: Nombre de la profesora asignada (ej: 'Emiliana', 'Brian'). Opcional.
    - nombre_o_tel_alumna: Nombre o teléfono de la alumna a dejar fija en ese horario. Opcional.
    """
    dias_map = {
        'lunes': 1, 'martes': 2, 'miercoles': 3, 'miércoles': 3,
        'jueves': 4, 'viernes': 5, 'sabado': 6, 'sábado': 6, 'domingo': 7
    }
    dia_num = 6
    for d_nom, d_v in dias_map.items():
        if d_nom in dia_semana_str.lower():
            dia_num = d_v
            break

    hora_clean = normalizar_hora_str(hora_str, dia_semana_str)
    h_i, m_i = map(int, hora_clean.split(':'))
    h_f = (h_i + 1) % 24
    t_inicio = datetime.time(h_i, m_i)
    t_fin = datetime.time(h_f, m_i)

    try:
        from core.models import Clase, PlantillaTurno, Turno
        clase_obj = Clase.objects.filter(is_active=True).first()
        if not clase_obj:
            return "✦ No hay una disciplina activa en el sistema para asociar la nueva plantilla."

        plantilla, created = PlantillaTurno.objects.get_or_create(
            clase=clase_obj,
            dia_semana=dia_num,
            hora_inicio=t_inicio,
            defaults={'hora_fin': t_fin, 'is_active': True}
        )
        if not created and not plantilla.is_active:
            plantilla.is_active = True
            plantilla.save(update_fields=['is_active'])

        prof_obj = None
        if nombre_profesora and nombre_profesora.strip():
            try:
                from plugins.profesores.backend.models import Profesor, PlantillaProfesor
                for p in Profesor.objects.filter(is_active=True).select_related('usuario'):
                    nom_full = f"{p.usuario.nombre} {p.usuario.apellido}".lower()
                    if nombre_profesora.lower() in nom_full:
                        prof_obj = p
                        break
                if prof_obj:
                    PlantillaProfesor.objects.update_or_create(
                        plantilla=plantilla,
                        defaults={'profesor': prof_obj}
                    )
            except Exception as ep:
                logger.warning(f"Error asignando profesor a plantilla: {ep}")

        # Generar turnos para los próximos 30 días en base a la plantilla
        from core.services import generar_turnos_desde_plantillas
        generar_turnos_desde_plantillas()

        # Si había turnos manuales ya creados sin plantilla en esa fecha/hora, vincularlos y asignarles la profesora
        turnos_coincidentes = Turno.objects.filter(
            clase=clase_obj,
            hora_inicio=t_inicio
        )
        for tc in turnos_coincidentes:
            if tc.fecha.isoweekday() == dia_num:
                if not tc.plantilla:
                    tc.plantilla = plantilla
                    tc.save(update_fields=['plantilla'])
                if prof_obj:
                    try:
                        from plugins.profesores.backend.models import TurnoProfesor
                        TurnoProfesor.objects.update_or_create(
                            turno=tc,
                            defaults={'profesor': prof_obj}
                        )
                    except Exception:
                        pass

        alumna_msg = ""
        if nombre_o_tel_alumna and nombre_o_tel_alumna.strip():
            alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
            if err == "multiples":
                return formatear_opciones_human_in_the_loop(
                    nombre_o_tel_alumna,
                    matches,
                    f"agregar al esquema semanal los {dia_semana_str} {hora_clean} hs"
                )
            if alumna:
                from plugins.recurrencias.backend.models import Recurrencia
                from plugins.recurrencias.backend.services import auto_agendar_recurrencias_usuario
                from plugins.membresias.backend.models import Suscripcion

                rec, r_created = Recurrencia.objects.get_or_create(
                    usuario=alumna,
                    clase=clase_obj,
                    dia_semana=dia_num,
                    hora_inicio=t_inicio,
                    defaults={'is_active': True}
                )
                if not r_created and not rec.is_active:
                    rec.is_active = True
                    rec.save(update_fields=['is_active'])

                sub = Suscripcion.objects.filter(usuario=alumna, estado='ACTIVO').order_by('-fecha_inicio').first()
                agendadas = 0
                if sub:
                    agendadas = auto_agendar_recurrencias_usuario(alumna, sub)
                alumna_msg = f"\n• *Alumna inscripta:* {alumna.nombre} {alumna.apellido} (se aseguraron automáticamente sus clases fijas de todos los sábados del mes en la Agenda)."

        dias_es = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
        dia_display = dias_es.get(dia_num, dia_semana_str.capitalize())
        prof_msg = f"\n• *Profesora a cargo:* {prof_obj.usuario.nombre} {prof_obj.usuario.apellido}" if prof_obj else ""

        return (
            f"✦ ¡Listo Deby! ✦\n\n"
            f"Cargué el nuevo horario al *Esquema Semanal*:\n"
            f"• *Día y horario fijo:* Todos los {dia_display}s a las {hora_clean} hs"
            f"{prof_msg}"
            f"{alumna_msg}\n"
            f"• *Estado:* Ya figura en el Esquema del panel web y los turnos de todos los {dia_display}s del mes quedaron generados en la Agenda."
        )
    except Exception as e:
        return f"✦ Ocurrió un error al agregar el horario al esquema: {e}"


@tool
def consultar_esquema_semanal_completo_duena(dia_semana_str: str = "") -> str:
    """
    Comando para la dueña: consulta la grilla completa del ESQUEMA SEMANAL (todas las clases fijas del estudio cargadas en la web).
    """
    try:
        from core.models import PlantillaTurno
        qs = PlantillaTurno.objects.filter(is_active=True).select_related('clase').order_by('dia_semana', 'hora_inicio')

        dias_map = {
            'lunes': 1, 'martes': 2, 'miercoles': 3, 'miércoles': 3,
            'jueves': 4, 'viernes': 5, 'sabado': 6, 'sábado': 6, 'domingo': 7
        }
        if dia_semana_str:
            for d_n, d_v in dias_map.items():
                if d_n in dia_semana_str.lower():
                    qs = qs.filter(dia_semana=d_v)
                    break

        if not qs.exists():
            return "✦ No hay horarios fijos cargados en el Esquema Semanal para ese período."

        dias_es = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
        lineas = ["✦ *Esquema Semanal de Violett Pilates:*\n"]
        dia_actual = None
        for p in qs:
            if p.dia_semana != dia_actual:
                dia_actual = p.dia_semana
                lineas.append(f"\n*{dias_es.get(p.dia_semana, f'Día {p.dia_semana}')}*")

            prof_txt = "Sin profesor asignado"
            try:
                from plugins.profesores.backend.models import PlantillaProfesor
                pp = PlantillaProfesor.objects.filter(plantilla_id=p.id).select_related('profesor__usuario').first()
                if pp and pp.profesor and pp.profesor.usuario:
                    prof_txt = f"Prof. {pp.profesor.usuario.nombre} {pp.profesor.usuario.apellido}".strip()
            except Exception:
                pass

            hora_fmt = p.hora_inicio.strftime('%H:%M')
            lineas.append(f"  • {hora_fmt} hs — {p.clase.nombre} ({prof_txt})")

        return "\n".join(lineas)
    except Exception as e:
        return f"✦ Ocurrió un error al consultar el esquema: {e}"


@tool
def dar_baja_horario_esquema_semanal_duena(dia_semana_str: str, hora_str: str) -> str:
    """
    Comando para la dueña: elimina o desactiva un horario fijo del ESQUEMA SEMANAL en la web.
    """
    dias_map = {
        'lunes': 1, 'martes': 2, 'miercoles': 3, 'miércoles': 3,
        'jueves': 4, 'viernes': 5, 'sabado': 6, 'sábado': 6, 'domingo': 7
    }
    dia_num = 1
    for d_nom, d_v in dias_map.items():
        if d_nom in dia_semana_str.lower():
            dia_num = d_v
            break

    hora_clean = normalizar_hora_str(hora_str, dia_semana_str)
    try:
        from core.models import PlantillaTurno
        h_i, m_i = map(int, hora_clean.split(':'))
        t_inicio = datetime.time(h_i, m_i)
        plantilla = PlantillaTurno.objects.filter(dia_semana=dia_num, hora_inicio=t_inicio, is_active=True).first()
        if not plantilla:
            return f"✦ No encontré una clase activa en el Esquema Semanal para el {dia_semana_str} a las {hora_clean} hs."

        plantilla.is_active = False
        plantilla.save(update_fields=['is_active'])

        dias_es = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
        dia_nom = dias_es.get(dia_num, dia_semana_str)
        return f"✦ ¡Listo Deby! Di de baja el horario del Esquema Semanal para los *{dia_nom}s a las {hora_clean} hs*."
    except Exception as e:
        return f"✦ Ocurrió un error al dar de baja el horario del esquema: {e}"


@tool
def enviar_mensaje_whatsapp_alumna_duena(nombre_o_tel_alumna: str, mensaje: str) -> str:
    """
    Comando exclusivo de la dueña (Deby) para enviar un mensaje directo de WhatsApp a una alumna
    (ej: 'Mandale un mensaje a Alex avisándole que va a tener la clase a las 5 de la tarde con Emiliana').
    Parámetros:
    - nombre_o_tel_alumna: Nombre, apellido o teléfono de la alumna (o vacío si se refiere a la alumna activa en contexto).
    - mensaje: Contenido del mensaje, aviso o instrucción para la alumna.
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return formatear_opciones_human_in_the_loop(nombre_o_tel_alumna, matches, f"enviarle el WhatsApp")
    elif not alumna:
        return f"✦ No encontré a ninguna alumna registrada como '{nombre_o_tel_alumna}' en Violett Pilates para enviarle el mensaje."

    clean_phone = getattr(alumna, 'telefono', None)
    if not clean_phone:
        try:
            from plugins.asistente.backend.models import ConversacionWhatsApp
            conv_prev = ConversacionWhatsApp.objects.filter(usuario=alumna).first()
            clean_phone = conv_prev.telefono if conv_prev else None
        except Exception:
            pass

    if not clean_phone:
        return f"✦ {alumna.nombre} {alumna.apellido} no tiene ningún número de teléfono registrado en el sistema."

    # Limpiar y formatear el mensaje con el tono cálido de Violett
    cuerpo = mensaje.strip()
    cuerpo = re.sub(r'^(?:avis[aá]ndole|dici[eé]ndole|comunic[aá]ndole|record[aá]ndole)\s+que\s+', '', cuerpo, flags=re.IGNORECASE)
    cuerpo = re.sub(r'^(?:mandale\s+un\s+mensaje\s+(?:a\s+[\w\s]+\s+)?(?:avis[aá]ndole\s+que|dici[eé]ndole\s+que|que)?)\s*', '', cuerpo, flags=re.IGNORECASE)
    cuerpo = re.sub(r'^(?:que|q)\s+', '', cuerpo, flags=re.IGNORECASE).strip()
    cuerpo = cuerpo[0].upper() + cuerpo[1:] if cuerpo else cuerpo

    nombre_dest = alumna.nombre or "Alumna"
    if any(k in cuerpo.lower() for k in ['¡hola', 'hola ', 'buenas']):
        texto_final = cuerpo
    else:
        texto_final = f"¡Hola {nombre_dest}! ✦ Te escribo desde Violett Pilates de parte de Deby: {cuerpo}"

    try:
        from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
        client = WhatsAppClient()
        client.send_text_message(clean_phone, texto_final)

        from plugins.asistente.backend.models import ConversacionWhatsApp, MensajeWhatsAppLog
        conv_alumna = ConversacionWhatsApp.objects.filter(telefono=clean_phone).first()
        if not conv_alumna:
            conv_alumna = ConversacionWhatsApp.objects.create(
                telefono=clean_phone,
                usuario=alumna,
                rol_detectado='CLIENTE'
            )
        MensajeWhatsAppLog.objects.create(
            conversacion=conv_alumna,
            direccion='SALIENTE',
            agente_responsable='agente_direccion',
            texto=texto_final
        )
        return (
            f"✦ ¡Listo Deby! Le envié el mensaje de WhatsApp a {alumna.nombre} {alumna.apellido} ({clean_phone}) ✦\n\n"
            f"Le escribí:\n"
            f"\"{texto_final}\""
        )
    except Exception as e:
        return f"✦ Ocurrió un error al enviar el WhatsApp a {alumna.nombre}: {e}"


@tool
def reprogramar_o_mover_reserva_alumna_duena(nombre_o_tel_alumna: str, fecha_origen: str, hora_origen: str, fecha_destino: str, hora_destino: str) -> str:
    """
    Comando para la dueña: mueve, cambia o reprograma la clase de una alumna a otro día u horario
    (ej: 'Cambiale la clase a Alex del sábado 17hs para el sábado a las 18hs', 'Pasá a Martina de mañana 18hs a las 19hs').
    Automáticamente libera la camilla anterior, reserva la nueva y le envía un WhatsApp avisándole a la alumna.
    """
    alumna, matches, err = buscar_alumna_flexible(nombre_o_tel_alumna)
    if err == "multiples":
        return formatear_opciones_human_in_the_loop(nombre_o_tel_alumna, matches, f"reprogramarle la clase")
    elif not alumna:
        return f"✦ No encontré a la alumna '{nombre_o_tel_alumna}' en el sistema."

    f_origen = resolver_fecha(fecha_origen)
    h_orig_clean = normalizar_hora_str(hora_origen, fecha_origen)
    h_orig_dt = resolver_hora(h_orig_clean) if h_orig_clean else None

    # Buscar reserva origen
    qs_res = Reserva.objects.filter(
        usuario=alumna,
        estado='CONFIRMADA',
        turno__fecha=f_origen
    ).select_related('turno', 'turno__clase')

    if h_orig_dt:
        qs_res = qs_res.filter(turno__hora_inicio__hour=h_orig_dt.hour, turno__hora_inicio__minute=h_orig_dt.minute)

    res_origen = qs_res.first()
    if not res_origen:
        return f"✦ No encontré ninguna reserva confirmada de {alumna.nombre} para el {f_origen.strftime('%d/%m')} a las {h_orig_clean} hs."

    turno_anterior = res_origen.turno

    # Resolver turno destino
    f_destino = resolver_fecha(fecha_destino)
    h_dest_clean = normalizar_hora_str(hora_destino, fecha_destino)
    h_dest_dt = resolver_hora(h_dest_clean) if h_dest_clean else None

    # Asegurar turnos
    try:
        from core.services import generar_turnos_desde_plantillas
        generar_turnos_desde_plantillas()
    except Exception:
        pass

    qs_turno_dest = Turno.objects.filter(fecha=f_destino, estado='PROGRAMADO')
    if h_dest_dt:
        qs_turno_dest = qs_turno_dest.filter(hora_inicio__hour=h_dest_dt.hour, hora_inicio__minute=h_dest_dt.minute)

    turno_destino = qs_turno_dest.first()
    if not turno_destino:
        # Intentar crear turno si no existe
        from core.models import Clase
        clase_def = Clase.objects.filter(is_active=True).first()
        h_i, m_i = map(int, h_dest_clean.split(':'))
        t_ini = datetime.time(h_i, m_i)
        t_fin = datetime.time((h_i + 1) % 24, m_i)
        turno_destino = Turno.objects.create(
            clase=clase_def,
            fecha=f_destino,
            hora_inicio=t_ini,
            hora_fin=t_fin,
            cupo_actual=2,
            estado='PROGRAMADO'
        )

    if turno_destino.cupo_actual <= 0:
        return f"✦ La clase de destino ({f_destino.strftime('%d/%m')} a las {h_dest_clean} hs) ya no tiene camillas libres."

    with transaction.atomic():
        # Cancelar origen
        res_origen.estado = 'CANCELADA_TIEMPO'
        res_origen.save()
        turno_anterior.cupo_actual += 1
        turno_anterior.save()

        # Crear destino
        res_nueva = Reserva.objects.create(
            turno=turno_destino,
            usuario=alumna,
            estado='CONFIRMADA'
        )
        turno_destino.cupo_actual = max(0, turno_destino.cupo_actual - 1)
        turno_destino.save()

        # Mantener o vincular suscripción
        try:
            from plugins.membresias.backend.models import ReservaMembresia
            rm = ReservaMembresia.objects.filter(reserva=res_origen).first()
            if rm:
                ReservaMembresia.objects.create(reserva=res_nueva, suscripcion=rm.suscripcion)
                rm.delete()
        except Exception:
            pass

    # Notificar a la alumna por WhatsApp
    try:
        from plugins.comunicaciones.backend.whatsapp_service import notificar_reprogramacion_alumna
        notificar_reprogramacion_alumna(alumna, turno_destino, turno_anterior)
    except Exception as ex_not:
        logger.warning(f"Error notificando reprogramación a {alumna.nombre}: {ex_not}")

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_dest_nom = dias_semana[f_destino.weekday()]
    return (
        f"✦ ¡Listo Deby! Moví la clase de {alumna.nombre} {alumna.apellido}:\n"
        f"• *Anterior:* {turno_anterior.fecha.strftime('%d/%m')} a las {turno_anterior.hora_inicio.strftime('%H:%M')} hs (camilla liberada)\n"
        f"• *Nuevo horario:* {dia_dest_nom} {f_destino.strftime('%d/%m')} a las {turno_destino.hora_inicio.strftime('%H:%M')} hs\n"
        f"• Le envié un mensaje de WhatsApp a {alumna.nombre} confirmándole el cambio 🌸."
    )


@tool
def mover_o_reprogramar_clase_completa_duena(
    fecha_origen: str,
    hora_origen: str,
    fecha_destino: str = "",
    hora_destino: str = "",
    avisar_alumnas: bool = True
) -> str:
    """
    Comando para la dueña: mueve o traslada una clase entera con todas sus alumnas inscriptas (tanto registradas como apartados manuales y alumnas con horario fijo recurrente) y su profesora
    a otro horario o fecha (ej: 'El lunes es feriado, necesito cambiar la clase de las 18 horas para las 10 de la mañana',
    'Pasar la clase del lunes 9 a las 18 horas para el lunes 9 a las 10 de la mañana con las mismas alumnas, la misma profesora').
    Automáticamente:
    1. Busca la clase original y todas las reservas (registradas, manuales y alumnas con recurrencia fija en ese día/horario).
    2. Crea o localiza la clase en el nuevo horario/fecha, conservando la profesora y disciplina.
    3. Traslada a todas las alumnas inscriptas sin cobrarles créditos adicionales ni perder apartados manuales.
    4. Cancela la clase del horario anterior para liberar la agenda.
    5. Actualiza exactamente los cupos de camillas para que refleje 100% la ocupación real.
    6. Envía un WhatsApp individual a cada alumna informando el traslado por feriado / reprogramación.
    """
    try:
        from core.models import Turno, Reserva, Clase, Usuario
    except ImportError:
        return "✦ Error interno: modelos del núcleo no disponibles."

    f_orig = resolver_fecha(fecha_origen)
    h_orig_clean = normalizar_hora_str(hora_origen, fecha_origen)
    h_orig_dt = resolver_hora(h_orig_clean) if h_orig_clean else None

    # Si fecha_destino no fue especificada o es vacía, asumimos la misma fecha_origen
    if not fecha_destino or not fecha_destino.strip() or fecha_destino.strip().lower() in ['mismo dia', 'mismo día', 'igual', 'el mismo']:
        f_dest = f_orig
    else:
        f_dest = resolver_fecha(fecha_destino)

    h_dest_clean = normalizar_hora_str(hora_destino, fecha_destino or fecha_origen)
    h_dest_dt = resolver_hora(h_dest_clean) if h_dest_clean else None

    if not h_orig_dt:
        return f"✦ No pude determinar la hora de origen ('{hora_origen}'). ¿A qué hora es la clase que querés cambiar?"
    if not h_dest_dt:
        return f"✦ No pude determinar la hora de destino ('{hora_destino}'). ¿A qué hora querés pasar la clase?"

    # 1. Buscar turno origen
    qs_orig = Turno.objects.filter(
        fecha=f_orig,
        hora_inicio__hour=h_orig_dt.hour,
        hora_inicio__minute=h_orig_dt.minute
    ).exclude(estado='CANCELADO').select_related('clase')

    turno_origen = qs_orig.first()
    if not turno_origen:
        turno_origen = Turno.objects.filter(
            fecha=f_orig,
            hora_inicio__hour=h_orig_dt.hour,
            hora_inicio__minute=h_orig_dt.minute
        ).first()

    if not turno_origen:
        return f"✦ No encontré ninguna clase programada para el {f_orig.strftime('%d/%m')} a las {h_orig_clean} hs."

    # Obtener profesora actual
    profesor_actual = None
    try:
        from plugins.profesores.backend.models import TurnoProfesor
        tp = TurnoProfesor.objects.filter(turno=turno_origen).select_related('profesor', 'profesor__usuario').first()
        if tp:
            profesor_actual = tp.profesor
    except Exception:
        pass

    # Obtener reservas activas en el turno origen (tanto registradas como manuales)
    reservas_confirmadas = list(Reserva.objects.filter(turno=turno_origen).exclude(estado__startswith='CANCELADA').select_related('usuario'))

    # Detectar también alumnas con Horario Fijo recurrente (Recurrencia) para este día y hora
    # (Muy importante: cubre alumnas como Nora cuyo plan haya vencido recientemente y por eso no tenían Reserva pre-creada)
    weekday = f_orig.isoweekday()
    alumnas_recurrentes_extra = []
    try:
        from plugins.recurrencias.backend.models import Recurrencia
        recs = Recurrencia.objects.filter(
            clase=turno_origen.clase,
            dia_semana=weekday,
            hora_inicio__hour=h_orig_dt.hour,
            hora_inicio__minute=h_orig_dt.minute,
            is_active=True
        ).select_related('usuario')
        for r in recs:
            if r.usuario and not any(res.usuario_id == r.usuario_id for res in reservas_confirmadas):
                alumnas_recurrentes_extra.append(r.usuario)
    except Exception as ex_rec:
        logger.warning(f"Error consultando recurrencias fijas en traslado: {ex_rec}")

    # 2. Buscar o crear turno destino
    qs_dest = Turno.objects.filter(
        fecha=f_dest,
        hora_inicio__hour=h_dest_dt.hour,
        hora_inicio__minute=h_dest_dt.minute
    ).exclude(estado='CANCELADO').first()

    if qs_dest:
        turno_destino = qs_dest
    else:
        clase_ref = turno_origen.clase
        h_i, m_i = h_dest_dt.hour, h_dest_dt.minute
        t_ini = datetime.time(h_i, m_i)
        t_fin = datetime.time((h_i + 1) % 24, m_i)
        turno_destino = Turno.objects.create(
            clase=clase_ref,
            fecha=f_dest,
            hora_inicio=t_ini,
            hora_fin=t_fin,
            cupo_actual=clase_ref.cupo_maximo,
            estado='PROGRAMADO'
        )

    # Asignar la misma profesora al turno destino si no tiene una
    if profesor_actual:
        try:
            from plugins.profesores.backend.models import TurnoProfesor
            TurnoProfesor.objects.update_or_create(
                turno=turno_destino,
                defaults={'profesor': profesor_actual}
            )
        except Exception as e_prof:
            logger.warning(f"Error reasignando profesora en turno destino: {e_prof}")

    # 3. Trasladar alumnas atómicamente
    alumnas_notificar = []
    nombres_trasladadas = []

    with transaction.atomic():
        # A) Trasladar reservas existentes (registradas y manuales)
        for res in reservas_confirmadas:
            res.estado = 'CANCELADA_TIEMPO'
            res.save(update_fields=['estado'])

            if res.usuario:
                res_nueva, _ = Reserva.objects.get_or_create(
                    turno=turno_destino,
                    usuario=res.usuario,
                    defaults={'estado': 'CONFIRMADA', 'tipo_reserva': res.tipo_reserva, 'es_recurrente': res.es_recurrente}
                )
                try:
                    from plugins.membresias.backend.models import ReservaMembresia
                    rm = ReservaMembresia.objects.filter(reserva=res).first()
                    if rm:
                        ReservaMembresia.objects.get_or_create(reserva=res_nueva, defaults={'suscripcion': rm.suscripcion})
                except Exception:
                    pass
                nombres_trasladadas.append(f"{res.usuario.nombre} {res.usuario.apellido}".strip())
                alumnas_notificar.append(res.usuario)
            else:
                # Alumna apartada manualmente sin cuenta
                Reserva.objects.create(
                    turno=turno_destino,
                    usuario=None,
                    nombre_temporal=res.nombre_temporal,
                    telefono_temporal=res.telefono_temporal,
                    tipo_reserva='MANUAL_TEMPORAL',
                    estado='CONFIRMADA'
                )
                nombres_trasladadas.append(f"{res.nombre_temporal} (manual)")

        # B) Trasladar alumnas con horario fijo recurrente que no tenían reserva puntual precreada (ej: plan por renovar como Nora)
        for u_rec in alumnas_recurrentes_extra:
            Reserva.objects.get_or_create(
                turno=turno_destino,
                usuario=u_rec,
                defaults={'estado': 'CONFIRMADA', 'tipo_reserva': 'REGISTRADO', 'es_recurrente': True}
            )
            saldo_info = ""
            try:
                from plugins.membresias.backend.models import Suscripcion
                susc = Suscripcion.objects.filter(usuario=u_rec, estado='ACTIVO').first()
                if not susc or susc.clases_restantes <= 0 or (susc.fecha_vencimiento and susc.fecha_vencimiento < f_dest):
                    saldo_info = " (recurrente - abono por renovar)"
            except Exception:
                pass
            nombres_trasladadas.append(f"{u_rec.nombre} {u_rec.apellido}".strip() + saldo_info)
            alumnas_notificar.append(u_rec)

        # Sincronizar cupo_actual real exacto del turno destino
        total_activas_dest = Reserva.objects.filter(turno=turno_destino).exclude(estado__startswith='CANCELADA').count()
        turno_destino.cupo_actual = max(0, turno_destino.clase.cupo_maximo - total_activas_dest)
        turno_destino.save(update_fields=['cupo_actual'])

        # Cancelar y liberar el turno origen
        turno_origen.estado = 'CANCELADO'
        turno_origen.cupo_actual = turno_origen.clase.cupo_maximo
        turno_origen.save(update_fields=['estado', 'cupo_actual'])

    # 4. Enviar WhatsApp a cada alumna registrada informando el cambio
    notificadas = []
    if avisar_alumnas and alumnas_notificar:
        try:
            from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
            from plugins.asistente.backend.models import ConversacionWhatsApp, MensajeWhatsAppLog
            client = WhatsAppClient()
            profe_txt = f" con la profe {profesor_actual.nombre}" if profesor_actual else ""

            for al in alumnas_notificar:
                clean_phone = getattr(al, 'telefono', None)
                if not clean_phone:
                    continue
                texto_msg = (
                    f"¡Hola {al.nombre}! ✦ Te avisamos desde Violett Pilates que por feriado, "
                    f"tu clase del {f_orig.strftime('%d/%m')} a las {turno_origen.hora_inicio.strftime('%H:%M')} hs "
                    f"fue trasladada para las {turno_destino.hora_inicio.strftime('%H:%M')} hs{profe_txt}. "
                    f"¡Tu lugar ya quedó asegurado automáticamente! Nos vemos en el estudio 🌸."
                )
                try:
                    client.send_text_message(clean_phone, texto_msg)
                    conv_alumna = ConversacionWhatsApp.objects.filter(telefono=clean_phone).first()
                    if not conv_alumna:
                        conv_alumna = ConversacionWhatsApp.objects.create(
                            telefono=clean_phone,
                            usuario=al,
                            rol_detectado='CLIENTE'
                        )
                    MensajeWhatsAppLog.objects.create(
                        conversacion=conv_alumna,
                        direccion='SALIENTE',
                        agente_responsable='agente_direccion',
                        texto=texto_msg
                    )
                    notificadas.append(al.nombre)
                except Exception as ex_w:
                    logger.warning(f"No se pudo enviar WhatsApp a {al.nombre}: {ex_w}")
        except Exception as e_w:
            logger.warning(f"Error en bloque de notificación de traslado: {e_w}")

    # 5. Respuesta ejecutiva para Deby
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_dest_nom = dias_semana[f_dest.weekday()]
    nombres_txt = ", ".join(nombres_trasladadas) if nombres_trasladadas else "Sin alumnas inscriptas"
    profe_nom = f"{profesor_actual.nombre} {profesor_actual.apellido}".strip() if profesor_actual else "Sin asignar"
    cupos_libres_txt = f"{turno_destino.cupo_actual} libre(s)" if turno_destino.cupo_actual > 0 else "Clase COMPLETA (0 libres)"

    res_final = (
        f"✦ ¡Listo Deby! Moví la clase completa con éxito ✦\n\n"
        f"• *Clase anterior:* {f_orig.strftime('%d/%m')} a las {turno_origen.hora_inicio.strftime('%H:%M')} hs (quedó CANCELADA y liberada)\n"
        f"• *Nuevo horario:* {dia_dest_nom} {f_dest.strftime('%d/%m')} a las {turno_destino.hora_inicio.strftime('%H:%M')} hs\n"
        f"• *Profesora:* {profe_nom}\n"
        f"• *Alumnas en la clase ({len(nombres_trasladadas)}):* {nombres_txt}\n"
        f"• *Disponibilidad:* {cupos_libres_txt}\n"
    )
    if notificadas:
        res_final += f"• Se les envió aviso por WhatsApp a: {', '.join(notificadas)} 🌸"

    return res_final
