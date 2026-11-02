import re
import logging
from .base import get_llm, extraer_texto

logger = logging.getLogger(__name__)

KEYWORDS_TURNOS = [
    r'\bturnos?\b', r'\bhorarios?\b', r'\bdisponib', r'\bcamillas?\b',
    r'\banotarme?\b', r'\breserv\w+', r'\bcancelo?\b', r'\bcancelar?\b',
    r'\breprogram\w+', r'\bmañana\b', r'\bhoy\b', r'\blunes\b', r'\bmartes\b',
    r'\bmi[eé]rcoles\b', r'\bjueves\b', r'\bviernes\b', r'\bs[aá]bado\b',
    r'\bagendad\w+', r'\bcupos?\b', r'\blugares?\b'
]

KEYWORDS_FINANZAS = [
    r'\bprecios?\b', r'\bcu[aá]nto (sale|cuesta)\b', r'\bvalor\b', r'\bcosto\b',
    r'\bplanes?\b', r'\babonos?\b', r'\bpagar?\b', r'\bpagos?\b',
    r'\btransfer\w+', r'\balias\b', r'\bcbu\b', r'\bcvu\b',
    r'\bcomprobantes?\b', r'\bcu[aá]ntas clases me quedan\b',
    r'\bcr[eé]ditos?\b', r'\bvencimiento\b'
]

KEYWORDS_PROFESORES = [
    r'\bmis clases\b', r'\bno puedo asistir\b', r'\bausencia\b',
    r'\bcubrir\b', r'\breemplazo\b', r'\bprofe\b'
]

KEYWORDS_DIRECCION = [
    r'\baprobar\b', r'\brechazar\b', r'\breporte\b', r'\bfacturaci[oó]n\b',
    r'\bocupaci[oó]n\b', r'\boptimizar\b', r'\bfusionar\b', r'\bmadre e hija\b',
    r'\binseparables?\b', r'\bprospectos?\b', r'\bm[eé]tricas?\b', r'\bpon[eé] a\b',
    r'\bsac[aá] a\b',
    r'\brenov\w+', r'\bcargale\b', r'\basignale\b', r'\bagregale\b',
    r'\banot[aá]\b', r'\banotale\b', r'\binscrib[ií]\b', r'\bcancelale\b',
    r'\babon[oó]\b', r'\bpag[oó]\b', r'\bplan nuevo\b', r'\bcu[aá]ntas clases le quedan\b',
    r'\bcrear\b', r'\bcre[aá]\b', r'\babrir\b', r'\babr[ií]\b', r'\bnueva clase\b', r'\bnuevo turno\b',
    r'\bagregar una clase\b', r'\bagreg[aá] una clase\b',
    r'\bagenda\b', r'\bqui[eé]nes vienen\b', r'\bficha\b', r'\balumna\b', r'\balumnas\b',
    r'\bmes entero\b', r'\btodo el mes\b', r'\bdel mes\b', r'\bde este mes\b',
    r'\bde la semana\b', r'\bingresos?\b', r'\brecaudaci[oó]n\b', r'\bbalance\b',
    r'\bcu[aá]nto (se factur[oó]|entr[oó]|ingres[oó]|se cobr[oó]|ganamos)\b',
    r'\bno de una semana\b', r'\bplata\b', r'\bdinero\b',
    r'\benero\b', r'\bfebrero\b', r'\bmarzo\b', r'\babril\b', r'\bmayo\b', r'\bjunio\b',
    r'\bjulio\b', r'\bagosto\b', r'\bseptiembre\b', r'\boctubre\b', r'\bnoviembre\b', r'\bdiciembre\b'
]

def clasificar_intencion_fast(texto: str, rol: str) -> str:
    """
    Clasificador heurístico ultra-rápido (0ms de latencia).
    """
    t = texto.lower().strip()

    # Si es la dueña (Deby): SIEMPRE a DIRECCIÓN ejecutiva (salvo saludo puramente social)
    if rol == 'DUENA':
        es_solo_saludo = any(t == s for s in ['hola', 'buenas', 'buen dia', 'buen día', 'buenas tardes', 'buenas noches', 'que tal', 'qué tal', 'hola!'])
        if es_solo_saludo:
            return 'agente_recepcionista'
        return 'agente_direccion'

    # Si es profesor
    if rol == 'PROFESOR':
        for pattern in KEYWORDS_PROFESORES:
            if re.search(pattern, t):
                return 'agente_profesores'

    # Turnos & Reservas (Alumnas y prospectos)
    for pattern in KEYWORDS_TURNOS:
        if re.search(pattern, t):
            return 'agente_turnos'

    # Finanzas & Pagos (Alumnas y prospectos)
    for pattern in KEYWORDS_FINANZAS:
        if re.search(pattern, t):
            return 'agente_finanzas'

    # Profesores
    for pattern in KEYWORDS_PROFESORES:
        if re.search(pattern, t):
            return 'agente_profesores'

    # Saludos o consultas generales
    return 'agente_recepcionista'

def router_node(state):
    """
    Nodo de Triaje / Orquestador.
    Evalúa el mensaje del usuario y determina a qué agente lego derivar la conversación.
    """
    messages = state["messages"]
    last_user_msg = ""
    for m in reversed(messages):
        if getattr(m, 'type', '') in ['human', 'user']:
            last_user_msg = extraer_texto(m.content) if hasattr(m, 'content') else str(m)
            break

    rol = state.get("rol", "PROSPECTO")
    
    # 1. Fast-path determinístico (<1ms)
    target = clasificar_intencion_fast(last_user_msg, rol)

    # 1b. Memoria conversacional para la dueña (Deby)
    # Si Deby venía conversando sobre reportes/dirección y su nuevo mensaje es un seguimiento
    # (ej: "del mes entero", "no de una semana", "y de octubre?", "pasame el resumen")
    if rol == 'DUENA' and target == 'agente_recepcionista' and len(messages) > 1:
        mensajes_previos = messages[:-1]
        for m in reversed(mensajes_previos[-4:]):
            prev_txt = extraer_texto(getattr(m, 'content', '')).lower()
            if any(k in prev_txt for k in ['facturaci', 'resumen ejecutivo', 'ingresos', 'ocupaci', 'reporte']):
                if any(k in last_user_msg.lower() for k in ['mes', 'semana', 'octubre', 'noviembre', 'todo', 'entero', 'no de', 'resumen', 'dame', 'pasame']):
                    target = 'agente_direccion'
                    break
    
    # 2. Si es recepcionista pero el mensaje tiene contenido analizable, evaluamos con LLM para triaje inteligente
    es_saludo_puro = any(last_user_msg.lower().strip() == s for s in ['hola', 'buenas', 'buen dia', 'buen día', 'buenas tardes', 'chau', 'gracias', 'dale', 'ok'])
    if target == 'agente_recepcionista' and not es_saludo_puro and len(last_user_msg.strip().split()) >= 2:
        llm = get_llm(tools=None, max_tokens=15, temperature=0.0)
        if llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                prompt_triaje = (
                    "Sos el clasificador de intenciones de Violett Pilates. "
                    "Respondé con UNA SOLA PALABRA entre: turnos, finanzas, direccion, recepcionista. "
                    "Si pide disponibilidad/cancelar/reservar/horarios/días -> turnos. "
                    "Si pide precios/pagos/alias/cbu/costo/planes -> finanzas. "
                    "Si es la dueña consultando balance, facturación, agregar clases o gestión de alumnas -> direccion. "
                    "Si sólo saluda o pregunta en general sobre el método -> recepcionista."
                )
                resp = llm.invoke([SystemMessage(content=prompt_triaje), HumanMessage(content=last_user_msg)])
                decision = extraer_texto(resp.content).strip().lower()
                if "turno" in decision:
                    target = "agente_turnos"
                elif "finanza" in decision or "precio" in decision or "pago" in decision:
                    target = "agente_finanzas"
                elif "direccion" in decision or "reporte" in decision:
                    target = "agente_direccion"
            except Exception as e:
                logger.warning(f"Error en triaje LLM: {e}")

    logger.info(f"[ORQUESTADOR MULTI-AGENTE] Mensaje: '{last_user_msg[:40]}...' -> Derivado a: {target} (Rol: {rol})")
    print(f"[ORQUESTADOR MULTI-AGENTE] Derivado a: {target} (Rol: {rol})", flush=True)

    return {
        "target_agent": target,
        "next_node": target
    }
