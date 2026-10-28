import logging
from langchain_core.messages import SystemMessage
from ..tools.reportes_tools import (
    obtener_reporte_facturacion_semanal,
    obtener_reporte_ocupacion_hoy,
    contactar_prospectos_desde_lista
)
from ..tools.optimizacion_tools import (
    analizar_optimizacion_turnos_proximos,
    vincular_alumnas_inseparables,
    guardar_preferencia_alumna,
    consultar_preferencias_o_vinculos
)
from ..tools.profesores_tools import (
    reasignar_profesora_directo,
    buscar_reemplazo_orden_duena
)
from ..tools.finanzas_tools import (
    aprobar_comprobante_pago,
    rechazar_comprobante_pago
)
from .base import get_llm, FORMATO_WHATSAPP_RULES, get_current_date_str

logger = logging.getLogger(__name__)

DIRECCION_TOOLS = [
    obtener_reporte_facturacion_semanal,
    obtener_reporte_ocupacion_hoy,
    analizar_optimizacion_turnos_proximos,
    reasignar_profesora_directo,
    buscar_reemplazo_orden_duena,
    vincular_alumnas_inseparables,
    aprobar_comprobante_pago,
    rechazar_comprobante_pago,
    contactar_prospectos_desde_lista,
    guardar_preferencia_alumna,
    consultar_preferencias_o_vinculos
]

SYSTEM_PROMPT_DIRECCION = """Sos el Agente Ejecutivo de Dirección y Optimización de Violett Pilates ✦.
Estás hablando directamente con Débora Zárate, la dueña y directora del estudio.
Tu tono es ejecutivo, resolutivo, prolijo, respetuoso y altamente eficaz.

COMANDOS Y CAPACIDADES EXCLUSIVAS DE LA DUEÑA:
- Fecha de referencia hoy: {fecha_hoy}
- Si la dueña aprueba un pago ("Aprobar [código]", "Acreditar a [nombre]" o simplemente "Aprobar"): usá 'aprobar_comprobante_pago'.
- Si pide rechazar un comprobante: usá 'rechazar_comprobante_pago'.
- Si la dueña pide reasignar una profesora directamente (ej: "El jueves a las 18 poné a Sofía en vez de Cande"): usá 'reasignar_profesora_directo'.
- Si pide buscar quién puede cubrir una clase: usá 'buscar_reemplazo_orden_duena'.
- Si consulta la ocupación o consolidación de clases (ej: "¿Cómo viene la ocupación?", "¿Hay clases con 1 sola alumna?"): usá 'analizar_optimizacion_turnos_proximos' o 'obtener_reporte_ocupacion_hoy'.
- Si consulta facturación o métricas de cobros: usá 'obtener_reporte_facturacion_semanal'.
- Si indica que dos alumnas vienen juntas o son inseparables (ej: "Marcela y Valentina son madre e hija"): usá 'vincular_alumnas_inseparables'.
- Si pide contactar prospectos: usá 'contactar_prospectos_desde_lista'.

{formato_rules}
"""

def agente_direccion_node(state):
    fecha_hoy = get_current_date_str()
    sys_prompt = SYSTEM_PROMPT_DIRECCION.format(
        fecha_hoy=fecha_hoy,
        formato_rules=FORMATO_WHATSAPP_RULES
    )

    llm = get_llm(tools=DIRECCION_TOOLS)
    if not llm:
        return {"messages": [], "agente_responsable": "agente_direccion"}

    messages = state["messages"]
    sys_msg = SystemMessage(
        content=sys_prompt,
        additional_kwargs={"cache_control": {"type": "ephemeral"}}
    )

    filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    full_messages = [sys_msg] + filtered_messages

    response = llm.invoke(full_messages)
    return {"messages": [response], "agente_responsable": "agente_direccion"}
