import logging
from langchain_core.messages import SystemMessage
from ..tools.finanzas_tools import (
    consultar_estado_plan_alumna,
    obtener_planes_y_precios,
    obtener_datos_transferencia_estudio,
    consultar_a_la_duena
)
from .base import get_llm, FORMATO_WHATSAPP_RULES, get_current_date_str

logger = logging.getLogger(__name__)

FINANZAS_TOOLS = [
    consultar_estado_plan_alumna,
    obtener_planes_y_precios,
    obtener_datos_transferencia_estudio,
    consultar_a_la_duena
]

SYSTEM_PROMPT_FINANZAS = """Sos el Agente Especialista en Planes, Membresías y Pagos de Violett Pilates ✦.
Tu objetivo es informar a las clientas y alumnas sobre los abonos disponibles, estado de sus créditos y medios de pago.

POLÍTICAS CLAVE DE MEMBRESÍAS Y PAGOS:
- Fecha de referencia hoy: {fecha_hoy}
- Si la alumna consulta cuántas clases le quedan o el vencimiento de su plan: usá 'consultar_estado_plan_alumna'.
- Si la clienta o prospecto consulta precios, abonos o planes: usá 'obtener_planes_y_precios'.
  * Destacá que el plan más elegido por la comunidad es el de 8 clases mensuales (2 veces por semana).
- Si solicitan datos bancarios para transferir: usá 'obtener_datos_transferencia_estudio'.
  * CERO ALUCINACIONES: NUNCA inventes un alias ni un CBU. Si no están configurados, decí con calidez que vas a consultarle a la dueña y usá 'consultar_a_la_duena'.
- Si la alumna quiere enviar un comprobante de pago, indicale que puede mandar la foto directamente por este chat de WhatsApp y el sistema lo procesará automáticamente.

{formato_rules}
"""

def agente_finanzas_node(state):
    fecha_hoy = get_current_date_str()
    sys_prompt = SYSTEM_PROMPT_FINANZAS.format(
        fecha_hoy=fecha_hoy,
        formato_rules=FORMATO_WHATSAPP_RULES
    )

    llm = get_llm(tools=FINANZAS_TOOLS)
    if not llm:
        return {"messages": [], "agente_responsable": "agente_finanzas"}

    messages = state["messages"]
    sys_msg = SystemMessage(
        content=sys_prompt,
        additional_kwargs={"cache_control": {"type": "ephemeral"}}
    )

    filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    full_messages = [sys_msg] + filtered_messages

    response = llm.invoke(full_messages)
    return {"messages": [response], "agente_responsable": "agente_finanzas"}
