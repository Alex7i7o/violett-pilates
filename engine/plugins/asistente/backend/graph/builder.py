import logging
import threading
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from ..agents import (
    router_node,
    agente_recepcionista_node,
    agente_turnos_node,
    agente_finanzas_node,
    agente_profesores_node,
    agente_direccion_node,
    TURNOS_TOOLS,
    FINANZAS_TOOLS,
    PROFESORES_TOOLS,
    DIRECCION_TOOLS
)

logger = logging.getLogger(__name__)

# Consolidación total de tools para el nodo ejecutor
ALL_ACTIVE_TOOLS = list({t.name: t for t in (TURNOS_TOOLS + FINANZAS_TOOLS + PROFESORES_TOOLS + DIRECCION_TOOLS)}.values())

def build_asistente_graph():
    """
    Construye el grafo orquestador multi-agente de Violett Pilates con arquitectura de legos:
    - Router / Triaje central
    - 4 Agentes Especialistas (Turnos, Finanzas, Profesores, Dirección)
    - 1 Agente Anfitrión / Recepcionista General
    - Capa desacoplada de ejecución de herramientas con aviso previo de espera activa
    """
    workflow = StateGraph(AgentState)

    # 1. Registrar nodos de agentes
    workflow.add_node("router", router_node)
    workflow.add_node("agente_recepcionista", agente_recepcionista_node)
    workflow.add_node("agente_turnos", agente_turnos_node)
    workflow.add_node("agente_finanzas", agente_finanzas_node)
    workflow.add_node("agente_profesores", agente_profesores_node)
    workflow.add_node("agente_direccion", agente_direccion_node)

    # 2. Registrar nodo de herramientas con Espera Activa desacoplada
    raw_tool_node = ToolNode(ALL_ACTIVE_TOOLS)

    def tools_wrapper_node(state: AgentState):
        ya_notificado = state.get("ack_enviado", False)
        if not ya_notificado:
            phone = state.get("phone")
            rol_user = state.get("rol", "")
            if phone:
                def _enviar_ack():
                    try:
                        from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
                        from ..models import MensajeWhatsAppLog, ConversacionWhatsApp
                        if rol_user == 'DUENA':
                            msg_ack = "✦ Aguardame un segundito que ya te preparo la información..."
                        else:
                            msg_ack = "¡Dale! ✦ Aguardame un segundito que ya me fijo en el sistema..."
                        print(f"[ASISTENTE ESPERA ACTIVA] Enviando aviso previo a {phone}...", flush=True)
                        WhatsAppClient().send_text_message(phone, msg_ack)
                        conv = ConversacionWhatsApp.objects.filter(telefono=phone).first()
                        if conv:
                            MensajeWhatsAppLog.objects.create(
                                conversacion=conv,
                                direccion='SALIENTE',
                                agente_responsable='asistente_espera_activa',
                                texto=msg_ack
                            )
                    except Exception as ex:
                        logger.warning(f"Error enviando ack de espera activa: {ex}")

                threading.Thread(target=_enviar_ack, daemon=True).start()

        tool_result = raw_tool_node.invoke(state)
        if isinstance(tool_result, dict):
            tool_result["ack_enviado"] = True
            return tool_result
        return {"messages": tool_result, "ack_enviado": True}

    workflow.add_node("tools", tools_wrapper_node)

    # 3. Punto de entrada
    workflow.set_entry_point("router")

    # 4. Enrutamiento condicional desde el Router
    def route_from_router(state: AgentState):
        return state.get("target_agent", "agente_recepcionista")

    workflow.add_conditional_edges("router", route_from_router, {
        "agente_turnos": "agente_turnos",
        "agente_finanzas": "agente_finanzas",
        "agente_profesores": "agente_profesores",
        "agente_direccion": "agente_direccion",
        "agente_recepcionista": "agente_recepcionista"
    })

    # 5. Condicional de continuación para agentes con herramientas
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return END

    # Recepcionista no tiene tools: finaliza directo
    workflow.add_edge("agente_recepcionista", END)

    # Agentes con tools
    for agent_node_name in ["agente_turnos", "agente_finanzas", "agente_profesores", "agente_direccion"]:
        workflow.add_conditional_edges(
            agent_node_name,
            should_continue,
            {"tools": "tools", END: END}
        )

    # 6. Retorno desde tools hacia el agente especialista que las invocó
    def route_from_tools(state: AgentState):
        return state.get("target_agent", "agente_recepcionista")

    workflow.add_conditional_edges("tools", route_from_tools, {
        "agente_turnos": "agente_turnos",
        "agente_finanzas": "agente_finanzas",
        "agente_profesores": "agente_profesores",
        "agente_direccion": "agente_direccion",
        "agente_recepcionista": END,
        END: END
    })

    return workflow.compile()
