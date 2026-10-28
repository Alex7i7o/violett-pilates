import logging
from langchain_core.messages import SystemMessage
from ..tools.profesores_tools import (
    consultar_mis_clases_profesor,
    gestionar_ausencia_y_buscar_reemplazo
)
from ..tools.turnos_tools import consultar_turnos_disponibles
from ..tools.finanzas_tools import consultar_a_la_duena
from .base import get_llm, FORMATO_WHATSAPP_RULES, get_current_date_str

logger = logging.getLogger(__name__)

PROFESORES_TOOLS = [
    consultar_mis_clases_profesor,
    gestionar_ausencia_y_buscar_reemplazo,
    consultar_turnos_disponibles,
    consultar_a_la_duena
]

SYSTEM_PROMPT_PROFESORES = """Sos el Agente Coordinador del Staff Docente de Violett Pilates ✦.
Tu objetivo es atender exclusivamente a las profesoras del estudio con profesionalismo, calidez y orden operativo.

POLÍTICAS PARA PROFESORAS:
- Fecha de referencia hoy: {fecha_hoy}
- Si la profesora consulta qué clases tiene asignadas hoy, mañana o en la semana: usá 'consultar_mis_clases_profesor'.
- Si la profesora avisa que no puede asistir o necesita reemplazo por enfermedad, urgencia o viaje: usá 'gestionar_ausencia_y_buscar_reemplazo'.
- Si necesita consultar turnos o disponibilidad de la grilla: usá 'consultar_turnos_disponibles'.
- Ante dudas administrativas o consultas a la dueña: usá 'consultar_a_la_duena'.

{formato_rules}
"""

def agente_profesores_node(state):
    fecha_hoy = get_current_date_str()
    sys_prompt = SYSTEM_PROMPT_PROFESORES.format(
        fecha_hoy=fecha_hoy,
        formato_rules=FORMATO_WHATSAPP_RULES
    )

    llm = get_llm(tools=PROFESORES_TOOLS)
    if not llm:
        return {"messages": [], "agente_responsable": "agente_profesores"}

    messages = state["messages"]
    sys_msg = SystemMessage(
        content=sys_prompt,
        additional_kwargs={"cache_control": {"type": "ephemeral"}}
    )

    filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    full_messages = [sys_msg] + filtered_messages

    response = llm.invoke(full_messages)
    return {"messages": [response], "agente_responsable": "agente_profesores"}
