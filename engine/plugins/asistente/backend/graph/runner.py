import os
import logging
from typing import Tuple, List
from django.utils import timezone

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from ..config_loader import get_brand_persona, get_asistente_config
from ..tools.turnos_tools import consultar_turnos_disponibles, reservar_camilla_turno, consultar_mis_reservas_alumna
from ..tools.finanzas_tools import consultar_estado_plan_alumna, obtener_planes_y_precios, obtener_datos_transferencia_estudio
from ..tools.profesores_tools import consultar_mis_clases_profesor, gestionar_ausencia_y_buscar_reemplazo
from ..tools.reportes_tools import obtener_reporte_facturacion_semanal, obtener_reporte_ocupacion_hoy, contactar_prospectos_desde_lista

logger = logging.getLogger(__name__)

# Lista consolidada de tools operativas
ALL_TOOLS = [
    consultar_turnos_disponibles,
    reservar_camilla_turno,
    consultar_mis_reservas_alumna,
    consultar_estado_plan_alumna,
    obtener_planes_y_precios,
    obtener_datos_transferencia_estudio,
    consultar_mis_clases_profesor,
    gestionar_ausencia_y_buscar_reemplazo,
    obtener_reporte_facturacion_semanal,
    obtener_reporte_ocupacion_hoy,
    contactar_prospectos_desde_lista
]

def build_system_prompt(rol: str, nombre_usuario: str, usuario_id: str) -> str:
    brand_persona = get_brand_persona()
    config = get_asistente_config()
    reglas = config.get('reglas_operativas', {})
    
    hoy_str = timezone.localdate().strftime('%A %d de %B de %Y')
    
    contexto_usuario = f"Estás hablando con: {nombre_usuario or 'Contacto nuevo'} (Rol: {rol})."
    if usuario_id:
        contexto_usuario += f" [ID Sistema: {usuario_id}]"

    return f"""{brand_persona}

---
REGLAS OPERATIVAS Y DE NEGOCIO:
- Fecha actual de referencia: {hoy_str}.
- Capacidad máxima estricta por turno: {reglas.get('max_cupo_por_turno', 3)} camillas de reformer (nunca sobrevender).
- Estructura de la sesión: {reglas.get('estructura_sesion', '55 minutos de clase + 5 minutos de ritual de descompresión')}.
- Dirección del estudio: {reglas.get('direccion', 'Gral. Guido 1573, Ramos Mejía')}.
- {contexto_usuario}

INSTRUCCIONES DE ATENCIÓN:
1. Usá siempre voseo argentino cordial, cálido y elegante ('vos', 'querés', 'fijate', 'sentite').
2. Colocá el destello ✦ con sutileza en saludos o despedidas.
3. Si el usuario te consulta por turnos, disponibilidad o reservas, utilizá las herramientas (tools) correspondientes antes de responder con datos inventados.
4. Si el usuario pide reservar, utilizá 'reservar_camilla_turno' pasando su usuario_id y el turno_id.
5. Si no tiene créditos para reservar, explicale amablemente el estado de su abono y ofrecé los planes disponibles o los datos de transferencia.
6. Mantené tus respuestas concisas, bien formateadas para leerse cómodamente en WhatsApp.
"""

def ejecutar_grafo_asistente(conversacion, mensaje_usuario: str) -> Tuple[str, str, List[str]]:
    """
    Ejecuta el ciclo de agente con LangGraph.
    Retorna: (texto_respuesta, agente_responsable, tools_ejecutadas)
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    
    nombre_user = ""
    usuario_id = ""
    if conversacion.usuario:
        nombre_user = f"{conversacion.usuario.nombre} {conversacion.usuario.apellido}".strip()
        usuario_id = str(conversacion.usuario.id)

    # 1. Modo Simulación si no hay API Key configurada
    if not api_key:
        logger.info("[ASISTENTE SIMULADOR] OPENAI_API_KEY no configurada. Ejecutando respuesta inteligente basada en reglas.")
        return _ejecutar_modo_simulacion(conversacion, mensaje_usuario, usuario_id, nombre_user)

    # 2. Modo LangGraph con OpenAI
    try:
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=api_key
        ).bind_tools(ALL_TOOLS)

        # Cargar historial reciente de la conversación (últimos 8 mensajes)
        mensajes_db = conversacion.mensajes.order_by('-created_at')[:8]
        historial_langchain = []
        for m in reversed(list(mensajes_db)):
            if m.direccion == 'ENTRANTE':
                historial_langchain.append(HumanMessage(content=m.texto))
            else:
                historial_langchain.append(AIMessage(content=m.texto))

        # Mensaje de sistema y nuevo mensaje del usuario
        sys_prompt = build_system_prompt(conversacion.rol_detectado, nombre_user, usuario_id)
        current_messages = [SystemMessage(content=sys_prompt)] + historial_langchain + [HumanMessage(content=mensaje_usuario)]

        # Definir grafo
        workflow = StateGraph(AgentState)

        def agente_node(state: AgentState):
            messages = state["messages"]
            response = llm.invoke(messages)
            return {"messages": [response], "agente_responsable": "asistente_recepcionista"}

        tool_node = ToolNode(ALL_TOOLS)

        workflow.add_node("agente", agente_node)
        workflow.add_node("tools", tool_node)

        def should_continue(state: AgentState):
            messages = state["messages"]
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            return END

        workflow.set_entry_point("agente")
        workflow.add_conditional_edges("agente", should_continue, {"tools": "tools", END: END})
        workflow.add_edge("tools", "agente")

        app = workflow.compile()

        initial_state: AgentState = {
            "messages": current_messages,
            "conversacion_id": str(conversacion.id),
            "phone": conversacion.telefono,
            "rol": conversacion.rol_detectado,
            "usuario_id": usuario_id,
            "nombre_usuario": nombre_user,
            "next_node": "agente",
            "agente_responsable": "asistente_recepcionista",
            "tools_usadas": [],
            "esperando_humano": False
        }

        final_output = app.invoke(initial_state)
        
        # Extraer respuesta final y tools ejecutadas
        tools_usadas = []
        respuesta_final = ""
        for m in final_output["messages"]:
            if isinstance(m, ToolMessage):
                tools_usadas.append(getattr(m, 'name', 'tool'))
            elif isinstance(m, AIMessage) and not m.tool_calls:
                respuesta_final = m.content

        if not respuesta_final:
            last_msg = final_output["messages"][-1]
            respuesta_final = last_msg.content if hasattr(last_msg, 'content') else "¡Hola! ✦ ¿En qué puedo acompañarte hoy?"

        return respuesta_final, "asistente_recepcionista", tools_usadas

    except Exception as e:
        logger.error(f"[ASISTENTE LLM ERROR] {e}", exc_info=True)
        # Fallback elegante
        return _ejecutar_modo_simulacion(conversacion, mensaje_usuario, usuario_id, nombre_user)


def _ejecutar_modo_simulacion(conversacion, mensaje_usuario: str, usuario_id: str, nombre_user: str) -> Tuple[str, str, List[str]]:
    """
    Modo fallback / simulador inteligente cuando no hay API Key o falla el proveedor LLM.
    Ejecuta las tools reales de Django según palabras clave.
    """
    msg_low = mensaje_usuario.lower()
    tools_usadas = []

    # 1. Consulta de turnos / horarios / disponibilidad
    if any(k in msg_low for k in ['turno', 'horario', 'disponib', 'clase', 'hoy', 'mañana', 'lugar', 'camilla']):
        fecha = 'hoy' if 'hoy' in msg_low else ('mañana' if 'mañana' in msg_low or 'manana' in msg_low else 'hoy')
        res = consultar_turnos_disponibles.invoke({"fecha_str": fecha})
        tools_usadas.append('consultar_turnos_disponibles')
        saludo = f"¡Hola {nombre_user}! ✦ " if nombre_user else "¡Hola! ✦ "
        return f"{saludo}Te comparto los horarios disponibles:\n\n{res}\n\nSi querés reservar alguna camilla, avisame cuál te queda mejor.", "agente_turnos_simulado", tools_usadas

    # 2. Consulta de plan / saldo / créditos
    if any(k in msg_low for k in ['plan', 'credito', 'clases que me quedan', 'vence', 'vencimiento', 'cuantas clases']):
        if usuario_id:
            res = consultar_estado_plan_alumna.invoke({"usuario_id": usuario_id})
            tools_usadas.append('consultar_estado_plan_alumna')
            return f"¡Hola {nombre_user}! ✦ Acá tenés los detalles de tu membresía:\n\n{res}", "agente_finanzas_simulado", tools_usadas
        else:
            res = obtener_planes_y_precios.invoke({})
            tools_usadas.append('obtener_planes_y_precios')
            return f"¡Hola! ✦ Te comparto nuestros planes vigentes:\n\n{res}", "agente_finanzas_simulado", tools_usadas

    # 3. Consulta de precios / transferencias
    if any(k in msg_low for k in ['precio', 'cuanto sale', 'costo', 'pagar', 'transfer', 'alias', 'cbu', 'datos']):
        planes = obtener_planes_y_precios.invoke({})
        datos = obtener_datos_transferencia_estudio.invoke({})
        tools_usadas.extend(['obtener_planes_y_precios', 'obtener_datos_transferencia_estudio'])
        return f"¡Hola! ✦ Con gusto te paso la información de valores y medios de pago:\n\n{planes}\n\n{datos}", "agente_finanzas_simulado", tools_usadas

    # 4. Saludo o consulta general
    saludo = f"¡Hola {nombre_user}! ✦ " if nombre_user else "¡Hola! ✦ "
    return f"{saludo}Bienvenida a Violett Pilates. Soy la asistente del estudio. Puedo ayudarte a consultar turnos disponibles en Reformer, reservar tu camilla, consultar el estado de tu plan o brindarte información de los abonos. ¿En qué puedo acompañarte hoy?", "asistente_recepcionista", tools_usadas
