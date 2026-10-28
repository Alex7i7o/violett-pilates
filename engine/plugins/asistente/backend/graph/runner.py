import os
import re
import time
import logging
from typing import Tuple, List

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from .state import AgentState
from .builder import build_asistente_graph, ALL_ACTIVE_TOOLS
from ..tools.turnos_tools import (
    consultar_turnos_disponibles,
    reservar_camilla_turno,
    consultar_mis_reservas_alumna,
    cancelar_reserva_alumna
)
from ..tools.finanzas_tools import (
    consultar_estado_plan_alumna,
    obtener_planes_y_precios,
    obtener_datos_transferencia_estudio,
    aprobar_comprobante_pago,
    rechazar_comprobante_pago,
    consultar_a_la_duena
)
from ..tools.profesores_tools import (
    consultar_mis_clases_profesor,
    gestionar_ausencia_y_buscar_reemplazo,
    reasignar_profesora_directo,
    buscar_reemplazo_orden_duena
)
from ..tools.optimizacion_tools import (
    analizar_optimizacion_turnos_proximos,
    vincular_alumnas_inseparables,
    guardar_preferencia_alumna,
    consultar_preferencias_o_vinculos
)
from ..tools.reportes_tools import (
    obtener_reporte_facturacion_semanal,
    obtener_reporte_ocupacion_hoy,
    contactar_prospectos_desde_lista
)

logger = logging.getLogger(__name__)

ALL_TOOLS = ALL_ACTIVE_TOOLS

_COMPILED_GRAPH = None

def get_compiled_graph():
    """Retorna la instancia compilada en memoria del grafo para evitar recompilaciones innecesarias"""
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_asistente_graph()
    return _COMPILED_GRAPH


def ejecutar_grafo_asistente(conversacion, mensaje_usuario: str) -> Tuple[str, str, List[str]]:
    """
    Ejecuta el ciclo de atención multi-agente con arquitectura de legos orquestada por LangGraph.
    Retorna: (texto_respuesta, agente_responsable, tools_ejecutadas)
    """
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')
    groq_key = os.environ.get('GROQ_API_KEY')

    nombre_user = ""
    usuario_id = ""
    if conversacion.usuario:
        nombre_user = f"{conversacion.usuario.nombre} {conversacion.usuario.apellido}".strip()
        usuario_id = str(conversacion.usuario.id)

    # 1. Modo Simulación si no hay API Key configurada
    if not anthropic_key and not openai_key and not groq_key:
        logger.info("[ASISTENTE SIMULADOR] Ni ANTHROPIC_API_KEY, ni OPENAI_API_KEY ni GROQ_API_KEY configuradas. Ejecutando respuesta inteligente basada en reglas.")
        return _ejecutar_modo_simulacion(conversacion, mensaje_usuario, usuario_id, nombre_user)

    # 2. Modo Orquestador Multi-Agente con LangGraph
    try:
        # Cargar historial reciente de la conversación (últimos 8 mensajes)
        mensajes_db = conversacion.mensajes.order_by('-created_at')[:8]
        historial_langchain = []
        for m in reversed(list(mensajes_db)):
            if m.direccion == 'ENTRANTE':
                historial_langchain.append(HumanMessage(content=m.texto))
            else:
                historial_langchain.append(AIMessage(content=m.texto))

        current_messages = historial_langchain + [HumanMessage(content=mensaje_usuario)]

        app = get_compiled_graph()

        initial_state: AgentState = {
            "messages": current_messages,
            "conversacion_id": str(conversacion.id),
            "phone": conversacion.telefono,
            "rol": conversacion.rol_detectado,
            "usuario_id": usuario_id,
            "nombre_usuario": nombre_user,
            "target_agent": None,
            "next_node": "router",
            "agente_responsable": "asistente_recepcionista",
            "tools_usadas": [],
            "esperando_humano": False
        }

        t_inicio = time.time()
        final_output = app.invoke(initial_state)
        duracion = time.time() - t_inicio

        # Extraer respuesta final y tools ejecutadas
        tools_usadas = []
        respuesta_final = ""
        agente_responsable = (
            final_output.get("agente_responsable") or 
            final_output.get("target_agent") or 
            "asistente_recepcionista"
        )

        for m in final_output.get("messages", []):
            if isinstance(m, ToolMessage):
                tools_usadas.append(getattr(m, 'name', 'tool'))
            elif isinstance(m, AIMessage) and not getattr(m, 'tool_calls', None):
                respuesta_final = m.content

        if not respuesta_final and final_output.get("messages"):
            last_msg = final_output["messages"][-1]
            respuesta_final = last_msg.content if hasattr(last_msg, 'content') else "¡Hola! ✦ ¿En qué puedo acompañarte hoy?"

        try:
            from ..services.formatter import sanitizar_para_whatsapp
            respuesta_final = sanitizar_para_whatsapp(respuesta_final)
        except Exception:
            pass

        print(f"[ASISTENTE TIMING] Multi-Agente completado en {duracion:.2f}s | Agente: {agente_responsable} | Tools: {tools_usadas}", flush=True)
        logger.info(f"[ASISTENTE TIMING] Multi-Agente completado en {duracion:.2f}s | Agente: {agente_responsable} | Tools: {tools_usadas}")

        return respuesta_final, agente_responsable, tools_usadas

    except Exception as e:
        logger.error(f"[ASISTENTE MULTI-AGENTE ERROR] {e}", exc_info=True)
        # Fallback elegante a simulador basado en reglas
        return _ejecutar_modo_simulacion(conversacion, mensaje_usuario, usuario_id, nombre_user)


def _ejecutar_modo_simulacion(conversacion, mensaje_usuario: str, usuario_id: str, nombre_user: str) -> Tuple[str, str, List[str]]:
    """
    Modo fallback / simulador inteligente cuando no hay API Key o falla el proveedor LLM.
    Ejecuta las tools reales de Django según palabras clave y rol detectado.
    """
    msg_low = mensaje_usuario.lower()
    tools_usadas = []
    rol = conversacion.rol_detectado

    # --- COMANDOS ADMINISTRATIVOS DE LA DUEÑA ---
    if rol == 'DUENA' or any(k in msg_low for k in ['aprobar', 'acreditar', 'rechazar']):
        # 1. Aprobación de comprobantes
        if any(k in msg_low for k in ['aprobar', 'acreditar']):
            partes = mensaje_usuario.split()
            identificador = ""
            for idx, p in enumerate(partes):
                if p.lower() in ['aprobar', 'acreditar', 'acredita', 'aprueba'] and idx + 1 < len(partes):
                    siguiente = partes[idx + 1].strip()
                    if siguiente.lower() not in ['el', 'la', 'un', 'una', 'a', 'comprobante', 'pago', 'plan']:
                        identificador = siguiente
                    elif idx + 2 < len(partes):
                        identificador = partes[idx + 2].strip()
                    break
            res = aprobar_comprobante_pago.invoke({"identificador": identificador})
            tools_usadas.append('aprobar_comprobante_pago')
            return res, "agente_finanzas_aprobacion", tools_usadas

        # 2. Rechazo de comprobantes
        if 'rechazar' in msg_low:
            res = rechazar_comprobante_pago.invoke({"identificador": ""})
            tools_usadas.append('rechazar_comprobante_pago')
            return res, "agente_finanzas_rechazo", tools_usadas

        # 3. Reasignación directa de profesoras (ej: "sacá a X y poné a Y", "reemplazá a X por Y")
        if any(k in msg_low for k in ['sacá a', 'saca a', 'poné a', 'pone a', 'reemplazá a', 'reemplaza a', 'en vez de']):
            match_saca_pone = re.search(r'(?:sac[aá]|reemplaz[aá])\s+(?:a\s+)?(\w+)\s+(?:y\s+)?(?:pon[eé]|por)\s+(?:a\s+)?(\w+)', msg_low)
            profe_ant = match_saca_pone.group(1) if match_saca_pone else ""
            nueva_profe = match_saca_pone.group(2) if match_saca_pone else ""
            
            hora_match = re.search(r'(\d{1,2}(?::\d{2})?(?:\s*hs)?)', msg_low)
            hora_str = hora_match.group(1) if hora_match else "18:00"
            
            fecha_str = "hoy"
            for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado', 'mañana', 'hoy']:
                if d in msg_low:
                    fecha_str = d
                    break

            res = reasignar_profesora_directo.invoke({
                "fecha_o_dia": fecha_str,
                "hora_str": hora_str,
                "profe_titular_nombre": profe_ant,
                "nueva_profe_nombre": nueva_profe
            })
            tools_usadas.append('reasignar_profesora_directo')
            return res, "agente_profesores_reasignacion", tools_usadas

        # 4. Búsqueda de quién puede cubrir
        if any(k in msg_low for k in ['quién puede', 'quien puede', 'fijate quién', 'fijate quien', 'cubrir a', 'reemplazo']):
            hora_match = re.search(r'(\d{1,2}(?::\d{2})?(?:\s*hs)?)', msg_low)
            hora_str = hora_match.group(1) if hora_match else "18:00"
            fecha_str = "hoy"
            for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado', 'mañana', 'hoy']:
                if d in msg_low:
                    fecha_str = d
                    break
            
            profe_match = re.search(r'(?:cubrir|reemplazar)\s+(?:a\s+)?(\w+)', msg_low)
            profe_nom = profe_match.group(1) if profe_match else ""

            res = buscar_reemplazo_orden_duena.invoke({
                "fecha_o_dia": fecha_str,
                "hora_str": hora_str,
                "profe_titular_nombre": profe_nom
            })
            tools_usadas.append('buscar_reemplazo_orden_duena')
            return res, "agente_profesores_cobertura", tools_usadas

        # 5. Análisis de ocupación y consolidación de horarios
        if any(k in msg_low for k in ['ocupacion', 'ocupación', 'consolidar', 'optimizar', 'clases solas', 'poca gente']):
            fecha_str = "mañana" if any(k in msg_low for k in ['mañana', 'manana']) else "hoy"
            res = analizar_optimizacion_turnos_proximos.invoke({"fecha_str": fecha_str})
            tools_usadas.append('analizar_optimizacion_turnos_proximos')
            return res, "optimizador_ocupacion", tools_usadas

        # 6. Registro de vínculos inseparables (ej: "Marcela y Valentina son madre e hija")
        if any(k in msg_low for k in ['madre e hija', 'inseparables', 'vienen juntas', 'amigas', 'juntas']):
            nombres_match = re.search(r'(\w+)\s+y\s+(\w+)', mensaje_usuario)
            if nombres_match:
                n1, n2 = nombres_match.group(1), nombres_match.group(2)
                res = vincular_alumnas_inseparables.invoke({
                    "alumna1_nombre_o_tel": n1,
                    "alumna2_nombre_o_tel": n2,
                    "observaciones": "Vienen juntas siempre (Registrado por indicación de la dueña)"
                })
                tools_usadas.append('vincular_alumnas_inseparables')
                return res, "asistente_preferencias", tools_usadas

        # 7. Reportes de facturación / métricas
        if any(k in msg_low for k in ['factur', 'ingreso', 'reporte', 'dinero', 'plata']):
            res = obtener_reporte_facturacion_semanal.invoke({})
            tools_usadas.append('obtener_reporte_facturacion_semanal')
            return res, "agente_reportes", tools_usadas

    # --- CONSULTAS DE PROFESORAS ---
    if rol == 'PROFESOR':
        if any(k in msg_low for k in ['mis clases', 'que clases tengo', 'horario']):
            res = consultar_mis_clases_profesor.invoke({"profesor_usuario_id": usuario_id})
            tools_usadas.append('consultar_mis_clases_profesor')
            return res, "agente_profesores", tools_usadas

    # --- CONSULTAS GENERALES / ALUMNAS ---
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
