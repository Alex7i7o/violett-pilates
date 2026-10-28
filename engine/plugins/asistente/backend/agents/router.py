import re
import logging
from .base import get_llm

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
    r'\bsac[aá] a\b'
]

def clasificar_intencion_fast(texto: str, rol: str) -> str:
    """
    Clasificador heurístico ultra-rápido (0ms de latencia).
    """
    t = texto.lower().strip()

    # Si es la dueña
    if rol == 'DUENA':
        for pattern in KEYWORDS_DIRECCION:
            if re.search(pattern, t):
                return 'agente_direccion'

    # Si es profesor
    if rol == 'PROFESOR':
        for pattern in KEYWORDS_PROFESORES:
            if re.search(pattern, t):
                return 'agente_profesores'

    # Turnos & Reservas
    for pattern in KEYWORDS_TURNOS:
        if re.search(pattern, t):
            return 'agente_turnos'

    # Finanzas & Pagos
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
            last_user_msg = m.content if hasattr(m, 'content') else str(m)
            break

    rol = state.get("rol", "PROSPECTO")
    
    # 1. Fast-path determinístico (<1ms)
    target = clasificar_intencion_fast(last_user_msg, rol)
    
    # 2. Si es recepcionista y el mensaje es complejo (>80 caracteres), evaluamos con LLM rápido
    if target == 'agente_recepcionista' and len(last_user_msg) > 80:
        llm = get_llm(tools=None, max_tokens=15, temperature=0.0)
        if llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                prompt_triaje = (
                    "Sos el clasificador de intenciones de Violett Pilates. "
                    "Respondé con UNA SOLA PALABRA entre: turnos, finanzas, recepcionista. "
                    "Si pide disponibilidad/cancelar/reservar -> turnos. "
                    "Si pide precios/pagos/alias/planes -> finanzas. "
                    "Si saluda o pregunta en general -> recepcionista."
                )
                resp = llm.invoke([SystemMessage(content=prompt_triaje), HumanMessage(content=last_user_msg)])
                decision = resp.content.strip().lower()
                if "turno" in decision:
                    target = "agente_turnos"
                elif "finanza" in decision or "precio" in decision or "pago" in decision:
                    target = "agente_finanzas"
            except Exception as e:
                logger.warning(f"Error en triaje LLM: {e}")

    logger.info(f"[ORQUESTADOR MULTI-AGENTE] Mensaje: '{last_user_msg[:40]}...' -> Derivado a: {target} (Rol: {rol})")
    print(f"[ORQUESTADOR MULTI-AGENTE] Derivado a: {target} (Rol: {rol})", flush=True)

    return {
        "target_agent": target,
        "next_node": target
    }
