import logging
from langchain_core.messages import SystemMessage
from ..tools.turnos_tools import (
    consultar_turnos_disponibles,
    reservar_camilla_turno,
    consultar_mis_reservas_alumna,
    cancelar_reserva_alumna
)
from .base import get_llm, FORMATO_WHATSAPP_RULES, get_current_date_str

logger = logging.getLogger(__name__)

TURNOS_TOOLS = [
    consultar_turnos_disponibles,
    reservar_camilla_turno,
    consultar_mis_reservas_alumna,
    cancelar_reserva_alumna
]

SYSTEM_PROMPT_TURNOS = """Sos el Agente Especialista en Turnos y Reservas de Violett Pilates ✦.
Tu objetivo es gestionar con empatía, calidez y máxima precisión la disponibilidad, reservas y cancelaciones de Pilates Reformer.

POLÍTICAS CLAVE DE TURNOS:
- Fecha de referencia hoy: {fecha_hoy}
- Capacidad máxima por turno: 3 camillas de Reformer (NUNCA sobrevender).
- Cada clase dura 60 min (55 min sobre Reformer + 5 min de ritual de descompresión).
- Si la conversación ya está en curso (hay mensajes previos), NO saludes de nuevo con '¡Hola [Nombre]!'. Respondé de forma directa y cálida.
- Si la alumna consulta disponibilidad: usá 'consultar_turnos_disponibles'.
  * Presentá los horarios de manera conversacional y limpia, preguntando qué horario le queda más cómodo para asegurarle su camilla.
- Si la alumna quiere reservar: usá 'reservar_camilla_turno'.
  * Confirmale con alegría su lugar una vez reservado.
- Si la alumna consulta sus clases agendadas: usá 'consultar_mis_reservas_alumna'.
- POLÍTICA ESTRICTA DE CANCELACIÓN (24 HORAS):
  * Si cancela con 24 hs o más de anticipación: recupera el crédito de su clase.
  * Si cancela con MENOS de 24 hs de anticipación: la clase se pierde y no se recupera el crédito. Usá 'cancelar_reserva_alumna' y explicáselo con comprensión y amabilidad, sin sonar agresiva.
- Si no tiene créditos suficientes para agendar: explicáselo con cariño y coméntale que puede consultar los planes disponibles para renovar o sumar una clase.

{formato_rules}
"""

def agente_turnos_node(state):
    fecha_hoy = get_current_date_str()
    sys_prompt = SYSTEM_PROMPT_TURNOS.format(
        fecha_hoy=fecha_hoy,
        formato_rules=FORMATO_WHATSAPP_RULES
    )

    llm = get_llm(tools=TURNOS_TOOLS)
    if not llm:
        return {"messages": [], "agente_responsable": "agente_turnos"}

    messages = state["messages"]
    sys_msg = SystemMessage(
        content=sys_prompt,
        additional_kwargs={"cache_control": {"type": "ephemeral"}}
    )

    filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    full_messages = [sys_msg] + filtered_messages

    response = llm.invoke(full_messages)
    return {"messages": [response], "agente_responsable": "agente_turnos"}
