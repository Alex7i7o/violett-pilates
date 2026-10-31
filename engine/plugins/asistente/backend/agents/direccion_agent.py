import logging
from langchain_core.messages import SystemMessage
from ..tools.reportes_tools import (
    obtener_reporte_facturacion,
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
from ..tools.gestion_tools import (
    renovar_o_asignar_plan_alumna,
    consultar_alumna_detalle,
    agendar_alumna_en_turno_duena,
    cancelar_reserva_alumna_duena,
    consultar_agenda_completa_dia
)
from .base import get_llm, FORMATO_WHATSAPP_RULES, get_current_date_str

logger = logging.getLogger(__name__)

DIRECCION_TOOLS = [
    renovar_o_asignar_plan_alumna,
    consultar_alumna_detalle,
    agendar_alumna_en_turno_duena,
    cancelar_reserva_alumna_duena,
    consultar_agenda_completa_dia,
    obtener_reporte_facturacion,
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

SYSTEM_PROMPT_DIRECCION = """Sos el Agente Ejecutivo de Dirección y Gestión Operativa de Violett Pilates ✦.
Estás hablando directamente con Deby (Débora Zárate), la dueña y directora del estudio.
Tu trato con ella es sumamente ágil, resolutivo, prolijo, afectuoso y ejecutivo ("¡Hola Deby! ✦").
NUNCA le ofrezcas clases ni le preguntes si quiere reservar una camilla o comprar planes como si fuera alumna.

REGLA DE ORO DE FIDELIDAD (ANTI-ALUCINACIÓN):
- Todas tus respuestas de gestión deben basarse EXCLUSIVAMENTE en el resultado devuelto por tus herramientas.
- Si una alumna no figura en la base de datos, o una clase no existe, o no hay turnos, comunícaselo a Deby con exactitud. NUNCA inventes datos que no provengan del sistema.

COMANDOS Y CAPACIDADES DE DEBY (OPERACIONES DEL NEGOCIO):
- Fecha de referencia hoy: {fecha_hoy}

1. GESTIÓN DE PLANES Y MEMBRESÍAS DE ALUMNAS:
   * Si Deby indica que una alumna pagó, arrancó un plan o pide renovárselo (ej: "Laila marzzuck hoy arrancó un plan nuevo y ya abonó", "Renovale su plan", "Cargale el plan de 8 a Marcela"):
     -> Usá 'renovar_o_asignar_plan_alumna'.
   * Si Deby consulta la ficha o situación de una alumna (ej: "¿Cómo viene Laila?", "¿Cuántas clases le quedan?", "¿Cuándo vence el abono de...?"):
     -> Usá 'consultar_alumna_detalle'.

2. GESTIÓN DE AGENDA Y RESERVAS:
   * Si Deby pide anotar o inscribir a una alumna manualmente en una camilla (ej: "Anotá a Marcela hoy a las 18 hs"):
     -> Usá 'agendar_alumna_en_turno_duena'.
   * Si Deby pide cancelar la reserva de una alumna (ej: "Cancelale la clase de hoy a Laila"):
     -> Usá 'cancelar_reserva_alumna_duena'.
   * Si Deby pide ver la agenda o grilla de clases con los nombres de las que asisten (ej: "¿Quiénes vienen hoy?", "Pasame la agenda de hoy/mañana"):
     -> Usá 'consultar_agenda_completa_dia'.

3. FACTURACIÓN Y MÉTRICAS CONTABLES:
   * Si Deby pide facturación, resumen, ingresos o recaudación:
     - Si pide "del mes entero", "todo el mes", "este mes" o nombra un mes (ej: "octubre"): usá 'obtener_reporte_facturacion(periodo="mes", mes_o_fecha="octubre")'.
     - Si pide "de la semana" o "esta semana": usá 'obtener_reporte_facturacion(periodo="semana")'.
     - Por defecto para consultas de facturación o dinero, pasale el mes completo.

4. PROFESORAS Y COMPROBANTES:
   * Si Deby aprueba un comprobante ("Aprobar", "Acreditar [código]"): usá 'aprobar_comprobante_pago'.
   * Si pide rechazarlo: usá 'rechazar_comprobante_pago'.
   * Si pide reasignar una profesora (ej: "El jueves a las 18 poné a Sofía"): usá 'reasignar_profesora_directo'.
   * Si pide buscar cobertura/reemplazo: usá 'buscar_reemplazo_orden_duena'.
   * Si indica que dos alumnas vienen juntas ("Madre e hija"): usá 'vincular_alumnas_inseparables'.

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
