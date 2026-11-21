import logging
import threading
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage

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
    DIRECCION_TOOLS,
    RECEPCIONISTA_TOOLS
)

logger = logging.getLogger(__name__)

# Consolidación total de tools para el nodo ejecutor
ALL_ACTIVE_TOOLS = list({t.name: t for t in (TURNOS_TOOLS + FINANZAS_TOOLS + PROFESORES_TOOLS + DIRECCION_TOOLS + RECEPCIONISTA_TOOLS)}.values())

def build_asistente_graph():
    """
    Construye el grafo orquestador multi-agente de Violett Pilates con arquitectura de legos:
    - Router / Triaje central
    - 4 Agentes Especialistas (Turnos, Finanzas, Profesores, Dirección)
    - 1 Agente Anfitrión / Recepcionista General
    - Capa desacoplada de herramientas con Espera Activa y Return-Direct Bypass (Ahorro 50% tokens)
    """
    workflow = StateGraph(AgentState)

    # 1. Registrar nodos de agentes
    workflow.add_node("router", router_node)
    workflow.add_node("agente_recepcionista", agente_recepcionista_node)
    workflow.add_node("agente_turnos", agente_turnos_node)
    workflow.add_node("agente_finanzas", agente_finanzas_node)
    workflow.add_node("agente_profesores", agente_profesores_node)
    workflow.add_node("agente_direccion", agente_direccion_node)

    # 2. Registrar nodo de herramientas con Espera Activa desacoplada y Bypass Return-Direct
    raw_tool_node = ToolNode(ALL_ACTIVE_TOOLS)

    def tools_wrapper_node(state: AgentState):
        ya_notificado = state.get("ack_enviado", False)
        cancel_event = threading.Event()
        if not ya_notificado:
            phone = state.get("phone")
            rol_user = state.get("rol", "")
            if phone:
                def _enviar_ack():
                    # Solo enviar ack si las tools demoran más de 2.5s (evita mensajes duplicados en respuestas rápidas)
                    if cancel_event.wait(timeout=2.5):
                        return
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
        cancel_event.set()

        # Determinar si la respuesta de la tool es auto-contenida (Return-Direct Bypass)
        mensajes_tools = tool_result.get("messages", []) if isinstance(tool_result, dict) else tool_result
        if not isinstance(mensajes_tools, list):
            mensajes_tools = [mensajes_tools]

        rol_user = state.get("rol", "")
        target_agent = state.get("target_agent", "")

        # Criterio Return-Direct:
        # NUNCA activar Return-Direct si:
        # 1. El usuario es la Dueña ('DUENA') o el agente es 'agente_direccion':
        #    Deby requiere soporte multitarea, razonamiento en cadena (iteración) y consolidación ejecutiva.
        # 2. Se ejecutaron múltiples tools (len(mensajes_tools) > 1):
        #    El LLM debe sintetizar y reportar el estado de cada tool/alumna ejecutada, nunca descartar las anteriores.
        es_respuesta_directa = False
        if target_agent != 'agente_direccion' and rol_user != 'DUENA' and len(mensajes_tools) == 1:
            ultimo_tool_msg = mensajes_tools[-1] if mensajes_tools else None
            texto_tool = getattr(ultimo_tool_msg, 'content', '') if ultimo_tool_msg else ''
            if isinstance(texto_tool, str) and len(texto_tool.strip()) >= 20:
                no_es_error_interno = not any(err_k in texto_tool.lower() for err_k in ['traceback', 'exception:', 'internal server error'])
                if no_es_error_interno:
                    es_respuesta_directa = True

        mensajes_salida = list(mensajes_tools)
        if es_respuesta_directa:
            mensajes_salida.append(AIMessage(content=texto_tool.strip()))
            logger.info(f"[LANGGRAPH RETURN-DIRECT] Bypass de 2da llamada activado para tool '{getattr(ultimo_tool_msg, 'name', 'tool')}'.")
            print(f"[LANGGRAPH RETURN-DIRECT] Bypass 2da llamada activado para '{getattr(ultimo_tool_msg, 'name', 'tool')}' (Ahorro: 50% tokens)", flush=True)

        return {
            "messages": mensajes_salida,
            "ack_enviado": True,
            "respuesta_directa": es_respuesta_directa
        }

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

    # Todos los agentes cuentan con tools o derivación
    for agent_node_name in ["agente_recepcionista", "agente_turnos", "agente_finanzas", "agente_profesores", "agente_direccion"]:
        workflow.add_conditional_edges(
            agent_node_name,
            should_continue,
            {"tools": "tools", END: END}
        )

    # 6. Retorno desde tools: si hubo Bypass Return-Direct, va a END; de lo contrario regresa al agente
    def route_from_tools(state: AgentState):
        if state.get("respuesta_directa"):
            return END
        last_m = state["messages"][-1] if state.get("messages") else None
        if isinstance(last_m, AIMessage) and not getattr(last_m, 'tool_calls', None):
            return END
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
