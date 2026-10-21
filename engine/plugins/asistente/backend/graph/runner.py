import os
import re
import logging
from typing import Tuple, List
from django.utils import timezone

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from ..config_loader import get_brand_persona, get_asistente_config
from ..tools.turnos_tools import consultar_turnos_disponibles, reservar_camilla_turno, consultar_mis_reservas_alumna
from ..tools.finanzas_tools import (
    consultar_estado_plan_alumna,
    obtener_planes_y_precios,
    obtener_datos_transferencia_estudio,
    aprobar_comprobante_pago,
    rechazar_comprobante_pago
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

# Lista consolidada de tools operativas para el agente
ALL_TOOLS = [
    # Turnos & Reservas
    consultar_turnos_disponibles,
    reservar_camilla_turno,
    consultar_mis_reservas_alumna,
    # Finanzas & Pagos
    consultar_estado_plan_alumna,
    obtener_planes_y_precios,
    obtener_datos_transferencia_estudio,
    aprobar_comprobante_pago,
    rechazar_comprobante_pago,
    # Profesores & Coberturas
    consultar_mis_clases_profesor,
    gestionar_ausencia_y_buscar_reemplazo,
    reasignar_profesora_directo,
    buscar_reemplazo_orden_duena,
    # Optimizador de Ocupación & Preferencias
    analizar_optimizacion_turnos_proximos,
    vincular_alumnas_inseparables,
    guardar_preferencia_alumna,
    consultar_preferencias_o_vinculos,
    # Reportes Ejecutivos & Prospección
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

    instrucciones_rol = ""
    if rol == 'DUENA':
        instrucciones_rol = """
COMANDOS EXCLUSIVOS DE LA DUEÑA / DIRECTORA:
- Si la dueña aprueba un pago diciendo "Aprobar {código}", "Acreditar a {nombre}", o simplemente "Aprobar", invocá inmediatamente 'aprobar_comprobante_pago'.
- Si la dueña indica un cambio directo de profesora (ej: "El jueves a las 18 sacá a Cande y poné a Julieta" o "Reemplazá a Mariana por Sofía"), invocá 'reasignar_profesora_directo'.
- Si la dueña pide buscar quién puede cubrir una clase (ej: "Fijate quién puede cubrir a Cande este martes a las 18"), invocá 'buscar_reemplazo_orden_duena'.
- Si la dueña consulta la ocupación o pide ver si hay clases para consolidar o juntar (ej: "¿Cómo viene la ocupación de mañana?", "¿Hay clases con 1 sola alumna?"), invocá 'analizar_optimizacion_turnos_proximos'.
- Si la dueña indica que dos alumnas vienen juntas o son inseparables (ej: "Anotá que Marcela y Valentina son madre e hija y vienen siempre juntas"), invocá 'vincular_alumnas_inseparables'.
- Si pide métricas o facturación, usá 'obtener_reporte_facturacion_semanal' u 'obtener_reporte_ocupacion_hoy'.
- Respondé a la dueña con tono ejecutivo, preciso, respetuoso y resolutivo.
"""
    elif rol == 'PROFESOR':
        instrucciones_rol = """
COMUNICACIÓN CON PROFESORAS:
- Si consulta sus clases, usá 'consultar_mis_clases_profesor'.
- Si avisa que no puede asistir un día u horario, usá 'gestionar_ausencia_y_buscar_reemplazo'.
"""

    return f"""{brand_persona}

---
REGLAS OPERATIVAS Y DE NEGOCIO:
- Fecha actual de referencia: {hoy_str}.
- Capacidad máxima estricta por turno: {reglas.get('max_cupo_por_turno', 3)} camillas de reformer (NUNCA sobrevender más de 3).
- Estructura de la sesión: {reglas.get('estructura_sesion', '55 minutos de clase + 5 minutos de ritual de descompresión')}.
- Dirección del estudio: {reglas.get('direccion', 'Gral. Guido 1573, Ramos Mejía')}.
- {contexto_usuario}
{instrucciones_rol}

INSTRUCCIONES DE ATENCIÓN:
1. Usá siempre voseo argentino cordial, cálido y elegante ('vos', 'querés', 'fijate', 'sentite').
2. Colocá el destello ✦ con sutileza en saludos o despedidas.
3. Si el usuario te consulta por turnos, disponibilidad o reservas, utilizá las herramientas (tools) correspondientes antes de responder.
4. Si una alumna pide reservar, utilizá 'reservar_camilla_turno' pasando su usuario_id y el turno_id.
5. Si no tiene créditos para reservar, explicale amablemente el estado de su abono y ofrecé los planes disponibles o los datos de transferencia.
6. Mantené tus respuestas concisas, bien formateadas para leerse cómodamente en WhatsApp.
"""

def ejecutar_grafo_asistente(conversacion, mensaje_usuario: str) -> Tuple[str, str, List[str]]:
    """
    Ejecuta el ciclo de agente con LangGraph.
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

    # 2. Modo LangGraph con LLM (Anthropic Claude, OpenAI GPT o Groq Llama)
    try:
        if anthropic_key:
            from langchain_anthropic import ChatAnthropic
            model_name = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-latest')
            llm = ChatAnthropic(
                model=model_name,
                temperature=0.3,
                api_key=anthropic_key
            ).bind_tools(ALL_TOOLS)
        elif openai_key:
            from langchain_openai import ChatOpenAI
            model_name = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
            llm = ChatOpenAI(
                model=model_name,
                temperature=0.3,
                api_key=openai_key
            ).bind_tools(ALL_TOOLS)
        else:
            from langchain_groq import ChatGroq
            model_name = os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b')
            llm = ChatGroq(
                model=model_name,
                temperature=0.3,
                api_key=groq_key
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
    Ejecuta las tools reales de Django según palabras clave y rol detectado.
    """
    msg_low = mensaje_usuario.lower()
    tools_usadas = []
    rol = conversacion.rol_detectado

    # --- COMANDOS ADMINISTRATIVOS DE LA DUEÑA ---
    if rol == 'DUENA' or any(k in msg_low for k in ['aprobar', 'acreditar', 'rechazar']):
        # 1. Aprobación de comprobantes
        if any(k in msg_low for k in ['aprobar', 'acreditar']):
            # Extraer posible identificador (palabra luego de aprobar/acreditar)
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
            # Extraer nombres mediante patrones comunes
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
            # Intentar extraer dos nombres
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
