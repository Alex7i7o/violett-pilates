import os
import re
import time
import logging
from typing import Tuple, List

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from .state import AgentState
from ..agents.base import extraer_texto
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
    obtener_reporte_facturacion,
    obtener_reporte_facturacion_semanal,
    obtener_reporte_ocupacion_hoy,
    contactar_prospectos_desde_lista
)
from ..tools.gestion_tools import (
    renovar_o_asignar_plan_alumna,
    consultar_alumna_detalle,
    agendar_alumna_en_turno_duena,
    cancelar_reserva_alumna_duena,
    consultar_agenda_completa_dia,
    crear_clase_y_agendar_alumna_duena,
    obtener_metricas_alumnas_duena,
    ajustar_creditos_alumna_duena,
    consultar_esquema_fijo_alumna,
    asignar_horario_fijo_alumna,
    dar_baja_horario_fijo_alumna,
    apartar_camilla_duena,
    liberar_camilla_bloqueada_duena,
    dar_baja_plan_alumna_duena,
    consultar_ultimas_resenas_duena,
    agregar_horario_esquema_semanal_duena,
    consultar_esquema_semanal_completo_duena,
    dar_baja_horario_esquema_semanal_duena,
    cancelar_o_eliminar_clase_agenda_duena,
    enviar_mensaje_whatsapp_alumna_duena,
    normalizar_hora_str,
    set_conversacion_activa,
    get_ultima_alumna_activa
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


def _procesar_confirmacion_hitl_si_aplica(conversacion, mensaje_usuario: str):
    set_conversacion_activa(conversacion)
    """
    Verifica si hay una acción pendiente esperando selección de alumna (Human-in-the-loop).
    Si el mensaje del usuario selecciona una opción ('1', 'la 1', 'laila', etc.), ejecuta la acción y limpia el estado.
    """
    if getattr(conversacion, 'rol_detectado', '') != 'DUENA':
        return None

    metadata = getattr(conversacion, 'metadata', None) or {}
    accion = metadata.get('accion_pendiente')
    if not accion:
        return None

    msg_low = mensaje_usuario.lower().strip()
    candidatos = accion.get('candidatos', [])
    if not candidatos:
        return None

    # Si Deby cancela o rechaza
    if any(k in msg_low for k in ['no', 'ninguna', 'ninguno', 'ningun', 'cancelar', 'cancelá', 'otra', 'ninguno de esos']):
        conversacion.metadata.pop('accion_pendiente', None)
        conversacion.save(update_fields=['metadata'])
        return (
            "Entendido Deby ✦. Cancelé la solicitud. Si querés pasame el apellido completo o teléfono de la alumna para buscarla nuevamente.",
            "agente_direccion",
            []
        )

    alumno_elegido = None

    # 1. Por número: '1', 'la 1', 'el 1', 'opción 1', 'primera', '2', 'segunda', etc.
    num_match = re.search(r'\b(?:la\s+|el\s+|opcion\s+|opción\s+)?([1-4])\b', msg_low)
    if num_match:
        idx = int(num_match.group(1)) - 1
        if 0 <= idx < len(candidatos):
            c_data = candidatos[idx]
            from core.models import Usuario
            alumno_elegido = Usuario.objects.filter(id=c_data['id']).first()

    # 2. Por ordinal en texto
    if not alumno_elegido:
        ordinales = {'primera': 0, 'primero': 0, 'segunda': 1, 'segundo': 1, 'tercera': 2, 'tercero': 2, 'cuarta': 3, 'cuarto': 3}
        for ord_txt, o_idx in ordinales.items():
            if ord_txt in msg_low and o_idx < len(candidatos):
                c_data = candidatos[o_idx]
                from core.models import Usuario
                alumno_elegido = Usuario.objects.filter(id=c_data['id']).first()
                break

    # 3. Por coincidencia de nombre o apellido
    if not alumno_elegido:
        from ..tools.gestion_tools import normalizar_texto_fonetico
        from core.models import Usuario
        for c_data in candidatos:
            nom_norm = normalizar_texto_fonetico(c_data.get('nombre', ''))
            palabras_msg = [p for p in normalizar_texto_fonetico(msg_low).split() if len(p) >= 3]
            if any(p in nom_norm for p in palabras_msg):
                alumno_elegido = Usuario.objects.filter(id=c_data['id']).first()
                break

    # 4. Si hay una sola opción y Deby dijo "sí" o "dale" o "esa"
    if not alumno_elegido and len(candidatos) == 1 and any(k in msg_low for k in ['si', 'sí', 'dale', 'esa', 'correcto', 'exacto', 'confirmado']):
        from core.models import Usuario
        alumno_elegido = Usuario.objects.filter(id=candidatos[0]['id']).first()

    if not alumno_elegido:
        # No coincide con una opción; si Deby preguntó otra cosa (ej: facturación, turnos), se descarta la acción pendiente
        return None

    # Ejecutar la acción guardada
    tipo = accion.get('tipo')
    params = accion.get('params', {})
    nom_completo = f"{alumno_elegido.nombre} {alumno_elegido.apellido}".strip()
    from ..tools.gestion_tools import registrar_alumna_activa
    registrar_alumna_activa(alumno_elegido)
    conversacion.metadata['alumna_activa'] = {
        'id': str(alumno_elegido.id),
        'nombre': nom_completo
    }

    # Limpiar acción pendiente
    conversacion.metadata.pop('accion_pendiente', None)
    conversacion.save(update_fields=['metadata'])

    if tipo == 'agendar':
        res = agendar_alumna_en_turno_duena.invoke({
            "nombre_o_tel_alumna": nom_completo,
            "fecha_o_dia": params.get('fecha_o_dia', 'hoy'),
            "hora_str": params.get('hora_str', '18:00')
        })
        return res, "agente_direccion", ['agendar_alumna_en_turno_duena']

    elif tipo == 'cancelar':
        res = cancelar_reserva_alumna_duena.invoke({
            "nombre_o_tel_alumna": nom_completo,
            "fecha_o_dia": params.get('fecha_o_dia', 'hoy'),
            "hora_str": params.get('hora_str', '')
        })
        return res, "agente_direccion", ['cancelar_reserva_alumna_duena']

    elif tipo == 'renovar_plan':
        res = renovar_o_asignar_plan_alumna.invoke({
            "nombre_o_tel_alumna": nom_completo,
            "nombre_o_clases_plan": params.get('nombre_o_clases_plan', '')
        })
        return res, "agente_direccion", ['renovar_o_asignar_plan_alumna']

    elif tipo == 'consultar_ficha':
        res = consultar_alumna_detalle.invoke({
            "nombre_o_tel": nom_completo
        })
        return res, "agente_direccion", ['consultar_alumna_detalle']

    elif tipo == 'crear_clase_y_agendar':
        res = crear_clase_y_agendar_alumna_duena.invoke({
            "nombre_o_tel_alumna": nom_completo,
            "fecha_o_dia": params.get('fecha_o_dia', 'hoy'),
            "hora_str": params.get('hora_str', '18:00')
        })
        return res, "agente_direccion", ['crear_clase_y_agendar_alumna_duena']

    elif tipo == 'consultar_esquema':
        res = consultar_esquema_fijo_alumna.invoke({"nombre_o_tel_alumna": nom_completo})
        return res, "agente_direccion", ['consultar_esquema_fijo_alumna']

    elif tipo == 'asignar_horario_fijo':
        res = asignar_horario_fijo_alumna.invoke({
            "nombre_o_tel_alumna": nom_completo,
            "dia_semana_str": params.get('dia_semana_str', 'lunes'),
            "hora_str": params.get('hora_str', '18:00')
        })
        return res, "agente_direccion", ['asignar_horario_fijo_alumna']

    elif tipo == 'dar_baja_horario_fijo':
        res = dar_baja_horario_fijo_alumna.invoke({"nombre_o_tel_alumna": nom_completo})
        return res, "agente_direccion", ['dar_baja_horario_fijo_alumna']

    elif tipo == 'dar_baja_plan':
        res = dar_baja_plan_alumna_duena.invoke({"nombre_o_tel_alumna": nom_completo})
        return res, "agente_direccion", ['dar_baja_plan_alumna_duena']

    elif tipo == 'ajustar_creditos':
        res = ajustar_creditos_alumna_duena.invoke({
            "nombre_o_tel_alumna": nom_completo,
            "cantidad_creditos": params.get('cantidad_creditos', 1),
            "motivo": params.get('motivo', 'Ajuste manual de la dueña')
        })
        return res, "agente_direccion", ['ajustar_creditos_alumna_duena']

    elif tipo == 'enviar_mensaje':
        res = enviar_mensaje_whatsapp_alumna_duena.invoke({
            "nombre_o_tel_alumna": nom_completo,
            "mensaje": params.get('mensaje', '')
        })
        return res, "agente_direccion", ['enviar_mensaje_whatsapp_alumna_duena']

    elif tipo == 'agregar_esquema':
        res = agregar_horario_esquema_semanal_duena.invoke({
            "dia_semana_str": params.get('dia_semana_str', 'sábado'),
            "hora_str": params.get('hora_str', '17:00'),
            "nombre_profesora": params.get('nombre_profesora', ''),
            "nombre_o_tel_alumna": nom_completo
        })
        return res, "agente_direccion", ['agregar_horario_esquema_semanal_duena']

    return None


def _guardar_hitl_si_corresponde(conversacion, texto_respuesta: str, tipo_accion: str, params: dict):
    """Si la respuesta le ofrece opciones de candidatas a Deby, guarda la acción pendiente para el próximo turno"""
    if not conversacion or getattr(conversacion, 'rol_detectado', '') != 'DUENA':
        return
    if "encontré estas posibles coincidencias" in texto_respuesta.lower() or "te referías a alguna" in texto_respuesta.lower():
        from ..tools.gestion_tools import get_ultimas_coincidencias_alumnas
        cands = get_ultimas_coincidencias_alumnas()
        if cands:
            conversacion.metadata['accion_pendiente'] = {
                'tipo': tipo_accion,
                'candidatos': [{'id': str(u.id), 'nombre': f"{u.nombre} {u.apellido}".strip(), 'telefono': getattr(u, 'telefono', '')} for u in cands],
                'params': params
            }
            conversacion.save(update_fields=['metadata'])


def ejecutar_grafo_asistente(conversacion, mensaje_usuario: str) -> Tuple[str, str, List[str]]:
    set_conversacion_activa(conversacion)
    """
    Ejecuta el ciclo de atención multi-agente con arquitectura de legos orquestada por LangGraph.
    Retorna: (texto_respuesta, agente_responsable, tools_ejecutadas)
    """
    # 0. Interceptar Human-in-the-loop si hay una selección de alumna pendiente
    res_hitl = _procesar_confirmacion_hitl_si_aplica(conversacion, mensaje_usuario)
    if res_hitl:
        return res_hitl

    gemini_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')
    groq_key = os.environ.get('GROQ_API_KEY')

    nombre_user = ""
    usuario_id = ""
    if conversacion.rol_detectado == 'DUENA':
        nombre_user = "Deby"
    elif conversacion.usuario:
        full_name = conversacion.usuario.nombre.strip() if conversacion.usuario.nombre else ""
        nombre_user = full_name.split()[0] if full_name else ""
        usuario_id = str(conversacion.usuario.id)
    else:
        from ..tools.gestion_tools import buscar_usuario_por_telefono
        u_auto = buscar_usuario_por_telefono(conversacion.telefono)
        if u_auto:
            conversacion.usuario = u_auto
            if conversacion.rol_detectado in ('PROSPECTO', ''):
                is_p = getattr(u_auto, 'is_profesor', False) or str(getattr(u_auto, 'rol', '')).upper() == 'PROFESOR'
                conversacion.rol_detectado = 'PROFESOR' if is_p else 'ALUMNA'
            conversacion.save(update_fields=['usuario', 'rol_detectado'])
            full_name = u_auto.nombre.strip() if u_auto.nombre else ""
            nombre_user = full_name.split()[0] if full_name else ""
            usuario_id = str(u_auto.id)

    # 1. Modo Simulación si no hay API Key configurada
    if not gemini_key and not anthropic_key and not openai_key and not groq_key:
        logger.info("[ASISTENTE SIMULADOR] Ninguna API Key configurada (GEMINI, GROQ, OPENAI, ANTHROPIC). Ejecutando respuesta conversacional inteligente basada en reglas.")
        return _ejecutar_modo_simulacion(conversacion, mensaje_usuario, usuario_id, nombre_user)

    # 2. Modo Orquestador Multi-Agente con LangGraph
    try:
        # Cargar historial previo optimizado (últimos 6 mensajes para ahorrar 60% de tokens de entrada)
        mensajes_db = list(conversacion.mensajes.order_by('-created_at')[1:7])
        historial_langchain = []
        for m in reversed(mensajes_db):
            # Los avisos de espera y errores técnicos no aportan contexto
            if m.agente_responsable in ('asistente_espera_activa', 'fallback_error', 'notificacion_duena'):
                continue
            if m.direccion == 'ENTRANTE':
                txt = m.texto.replace("🎤 [Audio]: ", "").strip()
                nuevo = HumanMessage(content=txt)
            else:
                # Comprimir respuestas históricas extensas para no re-enviar tablas gigantes en cada turno
                txt_resp = m.texto.strip()
                if len(txt_resp) > 400:
                    txt_resp = txt_resp[:400] + "... [resumido]"
                nuevo = AIMessage(content=txt_resp)
            if not nuevo.content:
                continue
            # Gemini exige turnos alternados: fusionamos mensajes consecutivos del mismo rol
            if historial_langchain and type(historial_langchain[-1]) is type(nuevo):
                historial_langchain[-1] = type(nuevo)(content=f"{historial_langchain[-1].content}\n{nuevo.content}")
            else:
                historial_langchain.append(nuevo)

        # El historial debe comenzar con un turno del usuario
        while historial_langchain and isinstance(historial_langchain[0], AIMessage):
            historial_langchain.pop(0)

        if historial_langchain and isinstance(historial_langchain[-1], HumanMessage):
            current_messages = historial_langchain[:-1] + [
                HumanMessage(content=f"{historial_langchain[-1].content}\n{mensaje_usuario}")
            ]
        else:
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
            "esperando_humano": False,
            "ack_enviado": False
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
                texto = extraer_texto(m.content)
                if texto:
                    respuesta_final = texto

        if not respuesta_final.strip():
            # El modelo no devolvió texto (respuesta vacía/bloqueada): usamos el simulador para no dejar a la persona sin respuesta
            logger.warning("[ASISTENTE] El LLM devolvió una respuesta vacía. Usando respuesta de respaldo.")
            return _ejecutar_modo_simulacion(conversacion, mensaje_usuario, usuario_id, nombre_user)

        try:
            from ..services.formatter import sanitizar_para_whatsapp
            respuesta_final = sanitizar_para_whatsapp(respuesta_final)
        except Exception:
            pass

        if "encontré estas posibles coincidencias" in respuesta_final.lower() or "te referías a alguna" in respuesta_final.lower():
            tipo_act = 'agendar'
            params_act = {}
            if 'cancelar_reserva_alumna_duena' in tools_usadas:
                tipo_act = 'cancelar'
            elif 'renovar_o_asignar_plan_alumna' in tools_usadas:
                tipo_act = 'renovar_plan'
            elif 'ajustar_creditos_alumna_duena' in tools_usadas:
                tipo_act = 'ajustar_creditos'
                m_cant = re.search(r'(\d+)\s*(?:cr[eé]ditos?|clases?)', mensaje_usuario.lower())
                params_act['cantidad_creditos'] = int(m_cant.group(1)) if m_cant else 1
                if any(k in mensaje_usuario.lower() for k in ['rest', 'descont', 'menos']):
                    params_act['cantidad_creditos'] = -abs(params_act['cantidad_creditos'])
            elif 'consultar_alumna_detalle' in tools_usadas:
                tipo_act = 'consultar_ficha'
            elif 'crear_clase_y_agendar_alumna_duena' in tools_usadas:
                tipo_act = 'crear_clase_y_agendar'
            elif 'consultar_esquema_fijo_alumna' in tools_usadas:
                tipo_act = 'consultar_esquema'
            elif 'asignar_horario_fijo_alumna' in tools_usadas:
                tipo_act = 'asignar_horario_fijo'
            elif 'dar_baja_horario_fijo_alumna' in tools_usadas:
                tipo_act = 'dar_baja_horario_fijo'
            elif 'dar_baja_plan_alumna_duena' in tools_usadas:
                tipo_act = 'dar_baja_plan'
            elif 'enviar_mensaje_whatsapp_alumna_duena' in tools_usadas:
                tipo_act = 'enviar_mensaje'
                params_act['mensaje'] = mensaje_usuario
            elif 'agregar_horario_esquema_semanal_duena' in tools_usadas:
                tipo_act = 'agregar_esquema'
            _guardar_hitl_si_corresponde(conversacion, respuesta_final, tipo_act, params_act)

        print(f"[ASISTENTE TIMING] Multi-Agente completado en {duracion:.2f}s | Agente: {agente_responsable} | Tools: {tools_usadas}", flush=True)
        logger.info(f"[ASISTENTE TIMING] Multi-Agente completado en {duracion:.2f}s | Agente: {agente_responsable} | Tools: {tools_usadas}")

        return respuesta_final, agente_responsable, tools_usadas

    except Exception as e:
        import traceback
        print(f"[ASISTENTE MULTI-AGENTE ERROR CRITICO] Fallback a simulador por error: {e}", flush=True)
        traceback.print_exc()
        logger.error(f"[ASISTENTE MULTI-AGENTE ERROR] Fallback a simulador conversacional por error: {e}", exc_info=True)
        try:
            from ..services.debugger_service import registrar_y_diagnosticar_error
            registrar_y_diagnosticar_error(
                conversacion=conversacion,
                mensaje_usuario=mensaje_usuario,
                excepcion=e,
                agente_responsable="orquestador_langgraph"
            )
        except Exception:
            pass
        return _ejecutar_modo_simulacion(conversacion, mensaje_usuario, usuario_id, nombre_user)


def _ejecutar_modo_simulacion(conversacion, mensaje_usuario: str, usuario_id: str, nombre_user: str) -> Tuple[str, str, List[str]]:
    """
    Modo simulador conversacional inteligente cuando no hay API Key o falla el proveedor LLM.
    Diseñado especialmente con alta empatía, voseo cariñoso, memoria del historial y trato cálido para personas adultas.
    Envuelto en protección a prueba de fallos para garantizar que NUNCA lance un fallback_error no controlado.
    """
    try:
        return _procesar_simulacion_interna(conversacion, mensaje_usuario, usuario_id, nombre_user)
    except Exception as sim_err:
        logger.error(f"[ASISTENTE SIMULACION ERROR] Excepción controlada en simulación: {sim_err}", exc_info=True)
        try:
            from ..services.debugger_service import registrar_y_diagnosticar_error
            respuesta_texto, _ = registrar_y_diagnosticar_error(
                conversacion=conversacion,
                mensaje_usuario=mensaje_usuario,
                excepcion=sim_err,
                agente_responsable="simulador_fallback"
            )
            return (respuesta_texto, "centinela_debugger", [])
        except Exception:
            pass

        rol = getattr(conversacion, 'rol_detectado', 'PROSPECTO')
        if rol == 'DUENA':
            return (
                f"✦ Deby, ocurrió un inconveniente consultando los datos del estudio: {sim_err}. Ya registré el aviso para revisarlo.",
                "agente_direccion",
                []
            )
        nombre_display = nombre_user.split()[0] if nombre_user else ""
        saludo = f"¡Hola {nombre_display}! ✦ " if nombre_display else "¡Hola! ✦ "
        return (
            f"{saludo}En este momento estoy actualizando la información del sistema. Si querés dejame tu consulta que en unos minutos te respondo con mucho gusto 🌸.",
            "asistente_recepcionista",
            []
        )


def _procesar_simulacion_interna(conversacion, mensaje_usuario: str, usuario_id: str, nombre_user: str) -> Tuple[str, str, List[str]]:
    set_conversacion_activa(conversacion)
    msg_low = mensaje_usuario.lower().strip()
    tools_usadas = []
    rol = conversacion.rol_detectado

    if rol == 'DUENA':
        nombre_display = "Deby"
    else:
        nombre_display = nombre_user.split()[0] if nombre_user else ""

    # Analizar historial para no repetir el saludo inicial ni hablar como un contestador
    mensajes_previos = list(conversacion.mensajes.order_by('-created_at')[:8])
    mensajes_salientes = [m for m in mensajes_previos if m.direccion == 'SALIENTE']
    ya_saludo_reciente = len(mensajes_salientes) > 0
    ultimo_mensaje_bot = mensajes_salientes[0].texto.lower() if mensajes_salientes else ""

    # El saludo con nombre solo se emite en el primerísimo contacto
    saludo_base = f"¡Hola {nombre_display}! ✦ " if (nombre_display and not ya_saludo_reciente) else ("¡Hola! ✦ " if not ya_saludo_reciente else "")

    # --- BLOQUEO DE SEGURIDAD ESTRICTO (ANTI-SUPLANTACIÓN Y ZERO-TRUST) ---
    es_intento_destructivo = any(k in msg_low for k in [
        'borra la base', 'borrar la base', 'borra toda', 'borrar toda', 'eliminar base',
        'drop table', 'delete from', 'vaciar base', 'wipe database', 'destruir base'
    ])
    if es_intento_destructivo:
        return (
            "Por políticas estrictas de seguridad del estudio, esa operación no existe ni está permitida en el sistema de Violett Pilates ✦.",
            "seguridad_bloqueo",
            []
        )

    # Si alguien afirma ser Deby pero no escribe desde su número oficial
    if any(k in msg_low for k in ['soy deby', 'soy debora', 'soy débora']) and rol != 'DUENA':
        return (
            "¡Hola! ✦ Por motivos de seguridad y privacidad del estudio, las funciones y reportes de dirección están asociados exclusivamente a la línea oficial de WhatsApp de Deby (11 5769-1786).\n\n"
            "Si sos Deby y estás escribiendo desde una nueva línea, por favor avisanos desde tu número principal así podemos actualizar tu registro y habilitarte todos los accesos de gestión 🌸.",
            "seguridad_bloqueo",
            []
        )

    # Si preguntan por Deby o la dueña
    if any(k in msg_low for k in ['quien es deby', 'quién es deby', 'quien es la dueña', 'quién es la dueña', 'esta deby', 'está deby', 'hablar con deby', 'hablar con la dueña', 'con debora', 'con débora', 'deby me dijo']):
        return (
            "Deby (Débora Zárate) es la fundadora y directora de Violett Pilates ✦, con más de 21 años de trayectoria enseñando el método y cuidando la salud postural de nuestras alumnas.\n\n"
            "Si querés dejarle un mensaje o necesitás que ella se comunique con vos de manera personalizada, avisame y se lo transmito con mucho gusto 🌸.",
            "asistente_recepcionista",
            []
        )

    # Consulta de capacidades ("qué podés hacer", "cómo funciona", "en qué me ayudás")
    es_consulta_capacidades = (
        bool(re.search(r'(?:qu[eé]|\bq\b)\s+(?:pod[eé]s\s+hacer|pod[eé]s|hac[eé]s|serv[ií]s|funciones|servicios|hacen)', msg_low)) or
        any(k in msg_low for k in [
            'como funciona', 'cómo funciona', 'para que servis', 'para qué servís',
            'en que me ayudas', 'en qué me ayudás', 'en q me ayudas', 'en q me ayudás',
            'que opciones hay', 'qué opciones hay', 'q opciones hay',
            'ayuda', 'como me ayudas', 'cómo me ayudás', 'como me podes ayudar', 'cómo me podés ayudar',
            'saber que podes hacer', 'saber q podes hacer', 'saber qué podés hacer', 'saber q podés hacer',
            'que sabes hacer', 'qué sabés hacer', 'q sabes hacer'
        ])
    )
    if es_consulta_capacidades:
        if rol == 'DUENA':
            return (
                "¡Hola Deby! ✦ Como tu asistente ejecutiva de Violett Pilates, podés gestionar todo el estudio directamente desde acá:\n\n"
                "• *Facturación e ingresos:* Consultar la recaudación del mes, suscripciones activas y desglose de abonos vendidos (ej: _\"Dame la facturación del mes\"_).\n"
                "• *Agenda y ocupación:* Ver la grilla completa de clases del día, quiénes asisten y camillas disponibles (ej: _\"Cómo viene la agenda de hoy\"_).\n"
                "• *Anotar alumnas en clases:* Inscribir alumnas en clases o moverlas de horario (ej: _\"Agendá a Alex para el sábado a las 17hs\"_).\n"
                "• *Abrir clases extraordinarias:* Si un horario no existe en la grilla regular, puedo crearlo en el momento y anotar a la alumna (ej: _\"Creá una clase el sábado 17hs y anotá a Alex\"_).\n"
                "• *Planes y abonos:* Consultar qué plan tiene una alumna o asignarle/renovarle uno (ej: _\"Qué plan tiene Alex\"_ o _\"Agrégale un plan de 4 clases a Alex\"_).\n"
                "• *Ficha de alumnas:* Ver su historial de asistencia, abono activo y notas (ej: _\"Ficha de Martina Filiel\"_).\n"
                "• *Comprobantes de pago:* Validar o acreditar transferencias enviadas por las alumnas.\n\n"
                "¿Qué necesitás revisar o gestionar ahora?",
                "agente_direccion",
                []
            )
        return (
            f"¡Con mucho gusto te cuento! ✦ Como asistente virtual de Violett Pilates puedo acompañarte en todo esto:\n\n"
            f"• *Consultar horarios:* Fijarme en tiempo real qué camillas Reformer tenemos libres para hoy, mañana o cualquier día de la semana.\n"
            f"• *Reservar o cancelar turnos:* Asegurar tu lugar en la clase que elijas o cancelar con anticipación si no podés asistir.\n"
            f"• *Tu abono y clases:* Decirte cuántas clases tenés disponibles en tu plan y cuándo vence.\n"
            f"• *Planes y precios:* Pasarte los valores de nuestros abonos mensuales y los datos para transferir.\n"
            f"• *Dudas y asesoramiento:* Explicarte cómo son las clases (55 min de Reformer + 5 min de ritual de descompresión asistido), dónde queda el estudio (Ramos Mejía) o transmitirte tranquilidad si tenés dolores de espalda o es tu primera vez 🌸.\n\n"
            f"¿Por cuál de estas cosas te gustaría que arranquemos?",
            "asistente_recepcionista",
            []
        )

    es_consulta_facturacion = any(k in msg_low for k in [
        'factur', 'ingreso', 'reporte de facturacion', 'reporte de facturación',
        'cuanta plata', 'cuánta plata', 'balance del mes', 'balance de la semana',
        'recaudacion', 'recaudación', 'ganancias', 'mes entero', 'todo el mes', 'del mes',
        'no de una semana'
    ])
    es_comando_admin = any(k in msg_low for k in [
        'aprobar comprobante', 'acreditar comprobante', 'rechazar comprobante',
        'sacá a', 'saca a', 'poné a', 'pone a', 'reemplazá a', 'reemplaza a'
    ])

    if (es_consulta_facturacion or es_comando_admin) and rol != 'DUENA':
        return (
            "Esa información y las acciones de gestión son confidenciales y de uso exclusivo de la dirección de Violett Pilates ✦. Si necesitás consultar los planes y valores vigentes para clientas, te los puedo compartir con mucho gusto.",
            "seguridad_bloqueo",
            []
        )

    # --- COMANDOS ADMINISTRATIVOS DE LA DUEÑA (AUTORIZACIÓN ESTRICTA) ---
    if rol == 'DUENA':
        # 0. Enviar mensaje de WhatsApp a una alumna por orden de la dueña
        es_orden_mensaje = any(k in msg_low for k in [
            'mandale un mensaje', 'mandale un whatsapp', 'mandale un wp', 'mandale un wpp',
            'avisale a', 'avisale por whatsapp', 'avisale por wp', 'escribile a',
            'mandale a'
        ])
        if es_orden_mensaje:
            # Buscar nombre tras 'a' o 'para'
            m_a_nom = re.search(r'(?:(?:mandale\s+(?:un\s+mensaje\s+)?a|avisale\s+a|escribile\s+a)\s+)([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:\s+(?:avisándole|diciéndole|que|q|para)|$|[?.,!])', mensaje_usuario, re.IGNORECASE)
            nom_target = m_a_nom.group(1).strip() if m_a_nom else ""
            if not nom_target:
                activa = get_ultima_alumna_activa()
                if activa:
                    nom_target = f"{activa.nombre} {activa.apellido}".strip()

            res = enviar_mensaje_whatsapp_alumna_duena.invoke({
                "nombre_o_tel_alumna": nom_target,
                "mensaje": mensaje_usuario
            })
            _guardar_hitl_si_corresponde(conversacion, res, 'enviar_mensaje', {'mensaje': mensaje_usuario})
            tools_usadas.append('enviar_mensaje_whatsapp_alumna_duena')
            return res, "agente_direccion", tools_usadas

        # 0. Esquema Semanal (agregar, consultar o dar de baja horarios fijos recurrentes en la web)
        es_orden_esquema = (
            any(k in msg_low for k in ['en el esquema', 'al esquema', 'esquema semanal', 'fija todos los', 'fijo todos los', 'fija todas las']) or
            ('esquema' in msg_low and any(k in msg_low for k in ['agreg', 'carg', 'pon', 'crea', 'met']))
        )
        if es_orden_esquema:
            dia_fijo = "sábado"
            for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado', 'domingo']:
                if d in msg_low:
                    dia_fijo = d
                    break

            hora_clean = normalizar_hora_str(msg_low, msg_low)
            # Si no encontró una hora explícita en este mensaje (ej: "Fijate que la clase del sábado no quedó en el esquema..."),
            # buscar si recientemente se habló de una clase a las 17hs o 5hs o si existe un turno creado
            if hora_clean == "18:00" and not any(k in msg_low for k in ['18', '6', '18hs', '18:00']):
                m_prev_hora = None
                if conversacion and hasattr(conversacion, 'mensajes'):
                    try:
                        for m_prev in conversacion.mensajes.all().order_by('-created_at')[:6]:
                            m_ph = re.search(r'\b(17(?::00)?|5(?:\s*de\s+la\s+tarde)?|11(?::00)?|9(?::00)?)\b', m_prev.texto.lower())
                            if m_ph:
                                m_prev_hora = m_ph.group(1)
                                break
                    except Exception:
                        pass
                if m_prev_hora:
                    hora_clean = normalizar_hora_str(m_prev_hora, "tarde")
                else:
                    try:
                        from core.models import Turno
                        dias_map_idx = {'lunes': 1, 'martes': 2, 'miercoles': 3, 'miércoles': 3, 'jueves': 4, 'viernes': 5, 'sabado': 6, 'sábado': 6}
                        d_num = dias_map_idx.get(dia_fijo.lower(), 6)
                        t_rec = Turno.objects.filter(fecha__gte=timezone.localdate(), estado='PROGRAMADO').order_by('-fecha')
                        for t in t_rec:
                            if t.fecha.isoweekday() == d_num:
                                hora_clean = t.hora_inicio.strftime('%H:%M')
                                break
                    except Exception:
                        pass

            # Profesora
            prof_nom = ""
            for p_cand in ['Emiliana', 'Brian', 'Sofia', 'Sofía', 'Deby', 'Debora', 'Débora']:
                if p_cand.lower() in msg_low:
                    prof_nom = p_cand
                    break
            if not prof_nom and conversacion and hasattr(conversacion, 'mensajes'):
                try:
                    for m_prev in conversacion.mensajes.all().order_by('-created_at')[:6]:
                        for p_cand in ['Emiliana', 'Brian', 'Sofia', 'Sofía']:
                            if p_cand.lower() in m_prev.texto.lower():
                                prof_nom = p_cand
                                break
                        if prof_nom:
                            break
                except Exception:
                    pass

            # Alumna
            nom_alumna = ""
            m_a = re.search(r'(?:para|con|alumna|alumno)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:$|[?.,!])', mensaje_usuario, re.IGNORECASE)
            if m_a:
                nom_alumna = m_a.group(1).strip()
            if not nom_alumna:
                activa = get_ultima_alumna_activa()
                if activa:
                    nom_alumna = f"{activa.nombre} {activa.apellido}".strip()

            res = agregar_horario_esquema_semanal_duena.invoke({
                "dia_semana_str": dia_fijo,
                "hora_str": hora_clean,
                "nombre_profesora": prof_nom,
                "nombre_o_tel_alumna": nom_alumna
            })
            _guardar_hitl_si_corresponde(conversacion, res, 'agregar_esquema', {'dia_semana_str': dia_fijo, 'hora_str': hora_clean, 'nombre_profesora': prof_nom})
            tools_usadas.append('agregar_horario_esquema_semanal_duena')
            return res, "agente_direccion", tools_usadas

        # 0. Reseñas y testimonios web
        if any(k in msg_low for k in ['reseñas', 'resenas', 'opiniones', 'calificaciones', 'estrellas', 'testimonios']):
            res = consultar_ultimas_resenas_duena.invoke({})
            tools_usadas.append('consultar_ultimas_resenas_duena')
            return res, "agente_direccion", tools_usadas

        # 0. Bloquear o apartar camilla
        if any(k in msg_low for k in ['apartar camilla', 'apartá una camilla', 'aparta una camilla', 'bloquear camilla', 'bloqueá una camilla', 'bloquea una camilla', 'apartar una camilla', 'bloqueo de camilla']):
            hora_m = re.search(r'(\d{1,2}(?::\d{2})?(?:\s*hs)?)', msg_low)
            hora_val = hora_m.group(1) if hora_m else "18:00"
            fecha_val = "mañana" if any(k in msg_low for k in ['mañana', 'manana']) else "hoy"
            for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado']:
                if d in msg_low:
                    fecha_val = d
                    break
            res = apartar_camilla_duena.invoke({"fecha_o_dia": fecha_val, "hora_str": hora_val, "motivo": "Reserva de dirección"})
            tools_usadas.append('apartar_camilla_duena')
            return res, "agente_direccion", tools_usadas

        # 0. Desbloquear o liberar camilla apartada
        if any(k in msg_low for k in ['desbloquear camilla', 'desbloqueá la camilla', 'desbloquea la camilla', 'liberar camilla bloqueada', 'liberar la camilla']):
            hora_m = re.search(r'(\d{1,2}(?::\d{2})?(?:\s*hs)?)', msg_low)
            hora_val = hora_m.group(1) if hora_m else "18:00"
            fecha_val = "mañana" if any(k in msg_low for k in ['mañana', 'manana']) else "hoy"
            for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado']:
                if d in msg_low:
                    fecha_val = d
                    break
            res = liberar_camilla_bloqueada_duena.invoke({"fecha_o_dia": fecha_val, "hora_str": hora_val})
            tools_usadas.append('liberar_camilla_bloqueada_duena')
            return res, "agente_direccion", tools_usadas

        # 0. Esquema fijo semanal (consulta o asignación)
        if any(k in msg_low for k in ['dias fijos', 'días fijos', 'horario fijo', 'horarios fijos', 'poner fija', 'poné fija', 'dejar fija', 'deja fija', 'sacale el horario fijo', 'borrá la recurrencia']):
            # Si pide sacar o borrar
            if any(k in msg_low for k in ['sacale', 'sacar', 'borra', 'borrá', 'elimina', 'eliminá', 'dar de baja']):
                m_nom = re.search(r'(?:sacale(?:\s+el)?\s+horario\s+fijo\s+a|borr[aá]\s+el\s+horario\s+fijo\s+de|baja\s+(?:a|de))\s+([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:$|[?.,!])', mensaje_usuario, re.IGNORECASE)
                nom_target = m_nom.group(1).strip() if m_nom else ""
                res = dar_baja_horario_fijo_alumna.invoke({"nombre_o_tel_alumna": nom_target or mensaje_usuario})
                _guardar_hitl_si_corresponde(conversacion, res, 'dar_baja_horario_fijo', {})
                tools_usadas.append('dar_baja_horario_fijo_alumna')
                return res, "agente_direccion", tools_usadas

            # Si pide asignar ("poné a Alex fija los sábados 11hs", "horario fijo para Marcela martes 18hs")
            es_asignar_fijo = any(k in msg_low for k in ['pone', 'poné', 'poner', 'asigna', 'asigná', 'asignar', 'deja', 'dejá', 'dejar', 'fija', 'fijo']) and any(d in msg_low for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado'])
            if es_asignar_fijo:
                dia_fijo = "lunes"
                for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado']:
                    if d in msg_low:
                        dia_fijo = d
                        break
                hora_m = re.search(r'(\d{1,2}(?::\d{2})?(?:\s*hs)?)', msg_low)
                hora_fijo = hora_m.group(1) if hora_m else "18:00"
                m_nom_fijo = re.search(r'(?:pon[eé]r?\s+(?:a\s+)?|horario\s+fijo\s+(?:para|a)\s+|dejar?\s+(?:a\s+)?)([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:\s+(?:fij[ao]|los|el|a\s+las|\d)|$|[?.,!])', mensaje_usuario, re.IGNORECASE)
                nom_target = m_nom_fijo.group(1).strip() if m_nom_fijo else ""
                nom_target = re.sub(r'\s+(?:para|en|el|la|de|a|fija|fijo)$', '', nom_target, flags=re.IGNORECASE).strip()
                res = asignar_horario_fijo_alumna.invoke({
                    "nombre_o_tel_alumna": nom_target or mensaje_usuario,
                    "dia_semana_str": dia_fijo,
                    "hora_str": hora_fijo
                })
                _guardar_hitl_si_corresponde(conversacion, res, 'asignar_horario_fijo', {'dia_semana_str': dia_fijo, 'hora_str': hora_fijo})
                tools_usadas.append('asignar_horario_fijo_alumna')
                return res, "agente_direccion", tools_usadas

            # Consulta ("¿Qué días fijos viene Martina?")
            m_nom_q = re.search(r'(?:d[ií]as\s+fijos\s+(?:tiene|de|viene)|horario\s+fijo\s+(?:tiene|de)|fija\s+)([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:$|[?.,!])', mensaje_usuario, re.IGNORECASE)
            nom_target = m_nom_q.group(1).strip() if m_nom_q else ""
            res = consultar_esquema_fijo_alumna.invoke({"nombre_o_tel_alumna": nom_target or mensaje_usuario})
            _guardar_hitl_si_corresponde(conversacion, res, 'consultar_esquema', {})
            tools_usadas.append('consultar_esquema_fijo_alumna')
            return res, "agente_direccion", tools_usadas

        # 0. Dar de baja plan o abono
        if any(k in msg_low for k in ['dar de baja el plan', 'dar de baja el abono', 'cancelale el plan', 'cancelale el abono', 'baja de su plan', 'baja de su abono', 'dar de baja su abono']):
            m_nom_baja = re.search(r'(?:plan\s+(?:de\s+)?|abono\s+(?:de\s+)?|a\s+)([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:$|[?.,!])', mensaje_usuario, re.IGNORECASE)
            nom_baja = m_nom_baja.group(1).strip() if m_nom_baja else ""
            nom_baja = re.sub(r'^(?:su|el|un)\s+(?:plan|abono)\s*', '', nom_baja, flags=re.IGNORECASE).strip()
            res = dar_baja_plan_alumna_duena.invoke({"nombre_o_tel_alumna": nom_baja or mensaje_usuario})
            _guardar_hitl_si_corresponde(conversacion, res, 'dar_baja_plan', {})
            tools_usadas.append('dar_baja_plan_alumna_duena')
            return res, "agente_direccion", tools_usadas
        # 0g. Consulta de cantidad y métricas de alumnas
        es_consulta_cantidad_alumnas = (
            any(k in msg_low for k in [
                'cantidad de alumnas', 'cantidad de clientas', 'cuántas alumnas', 'cuantas alumnas',
                'cuántas clientas', 'cuantas clientas', 'alumnas que tenemos', 'alumnas tenemos',
                'alumnas activas', 'total de alumnas', 'total alumnas', 'alumnas anotadas en total',
                'población de alumnas', 'poblacion de alumnas', 'alumnas inscriptas en total'
            ]) or
            bool(re.search(r'\b(?:la\s+)?cantidad\s+(?:de\s+)?alumnas?\b', msg_low)) or
            bool(re.search(r'\bcu[aá]ntas?\s+(?:alumnas?|clientas?)\b', msg_low))
        )
        if es_consulta_cantidad_alumnas:
            res = obtener_metricas_alumnas_duena.invoke({})
            tools_usadas.append('obtener_metricas_alumnas_duena')
            return res, "agente_direccion", tools_usadas

        # 0h. Ajustar créditos sueltos a una alumna (ej: "Agrégale 4 clases", "Ponele 4 créditos más", "Sumale 1 clase")
        es_ajuste_creditos = (
            any(k in msg_low for k in [
                'sumale una clase', 'sumale 1 clase', 'sumale 2 clases', 'sumale 4 clases',
                'restale una clase', 'restale 1 clase', 'clase de regalo', 'clase de cortesía', 'clase de cortesia',
                'creditos mas', 'créditos mas', 'creditos más', 'créditos más'
            ]) or
            bool(re.search(r'\b(?:agr[eé]g|s[uú]m|p[oó]n|c[aá]rg|d[aá]|rest)\w*\s+(?:le\s+)?(\d+)\s*(?:cr[eé]ditos?|clases?)', msg_low)) or
            (('sumale' in msg_low or 'restale' in msg_low or 'agregale' in msg_low or 'agrégale' in msg_low or 'ponele' in msg_low or 'cargale' in msg_low) and any(k in msg_low for k in ['clase', 'clases', 'credito', 'crédito', 'creditos', 'créditos']))
        )
        if es_ajuste_creditos and not ('plan' in msg_low):
            m_cant = re.search(r'(\d+)\s*(?:cr[eé]ditos?|clases?)', msg_low)
            cant = int(m_cant.group(1)) if m_cant else 1
            if any(k in msg_low for k in ['rest', 'descont', 'menos']):
                cant = -abs(cant)
            m_nom = re.search(r'(?:(?:a|para)\s+)([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:\s+(?:hoy|el|con|por|\d)|$|[?.,!])', mensaje_usuario, re.IGNORECASE)
            nom = m_nom.group(1).strip() if m_nom else ""
            nom = re.sub(r'\s+(?:para|en|el|la|de|a|este|esta|su|un)$', '', nom, flags=re.IGNORECASE).strip()
            if nom.lower() in ['un', 'el', 'su', 'la', 'clase', 'clases', 'credito', 'creditos', 'crédito', 'créditos', 'mas', 'más']:
                nom = ""

            if not nom:
                activa = get_ultima_alumna_activa()
                if activa:
                    nom = f"{activa.nombre} {activa.apellido}".strip()

            res = ajustar_creditos_alumna_duena.invoke({"nombre_o_tel_alumna": nom or mensaje_usuario, "cantidad_creditos": cant})
            _guardar_hitl_si_corresponde(conversacion, res, 'ajustar_creditos', {'cantidad_creditos': cant})
            tools_usadas.append('ajustar_creditos_alumna_duena')
            return res, "agente_direccion", tools_usadas

        # 0. Renovación o asignación de plan a una alumna
        es_orden_plan = (
            any(k in msg_low for k in ['renov', 'cargale', 'asignale', 'arrancó un plan', 'arranco un plan', 'abonó hoy', 'abono hoy', 'pagó hoy', 'pago hoy', 'plan nuevo', 'ya abonó', 'ya abono']) or
            bool(re.search(r'\b(?:agr[eé]g|s[uú]m|c[aá]rg|as[ií]gn|p[oó]n|r[eé]n[oó]v)\w*\s+(?:un\s+plan|el\s+plan|plan)', msg_low)) or
            ('plan' in msg_low and any(k in msg_low for k in ['agreg', 'agrég', 'sum', 'carg', 'cárg', 'asign', 'asígn', 'pon', 'pón', 'renov', 'ponele', 'ponerle', 'agregale', 'agrégale', 'agregarle', 'sumale', 'sumarle']))
        )
        if es_orden_plan:
            m_clases = re.search(r'\b(1|4|8|12|16)\s*clases?', msg_low)
            clases_target = m_clases.group(0) if m_clases else ""
            if not clases_target:
                m_num = re.search(r'plan\s+(?:de\s+)?(\d{1,2})', msg_low)
                if m_num:
                    clases_target = m_num.group(1)

            nombre_target = ""
            # Buscar nombre tras conectores como "a [Nombre]" o "a la alumna [Nombre]"
            m_a_nom = re.search(r'(?:(?:plan\s+(?:de\s+)?\d+\s*clases?|el\s+plan|un\s+plan)\s+a\s+|(?:\s+a\s+))([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:\s+(?:hoy|el|con|de|\$|\d)|$|[?.,!])', mensaje_usuario, re.IGNORECASE)
            if m_a_nom:
                cand = m_a_nom.group(1).strip()
                if cand.lower() not in ['un', 'el', 'su', 'la', 'un plan', 'el plan', 'su plan', 'clases']:
                    nombre_target = cand

            if not nombre_target:
                m_renov = re.search(r'(?:renov[aá](?:le)?(?:\s+el\s+plan)?(?:\s+a)?|cargale(?:\s+el\s+plan)?(?:\s+a)?|asignale(?:\s+el\s+plan)?(?:\s+a)?|agreg[aá](?:le)?(?:\s+el\s+plan)?(?:\s+a)?)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:\s+(?:hoy|el|con|de|\$|\d)|$|[?.,!])', mensaje_usuario, re.IGNORECASE)
                if m_renov and m_renov.group(1).strip().lower() not in ['su', 'su plan', 'el plan', 'un plan']:
                    nombre_target = m_renov.group(1).strip()
                elif any(k in msg_low for k in ['arrancó', 'arranco', 'abonó', 'abono', 'pagó', 'pago']):
                    m_arranco = re.search(r'^([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)\s+(?:hoy|arranc|abon|pag)', mensaje_usuario, re.IGNORECASE)
                    if m_arranco:
                        nombre_target = m_arranco.group(1).strip()

            if nombre_target:
                nombre_target = re.sub(r'^(?:un|el|su)\s+plan(?:\s+de)?\s*', '', nombre_target, flags=re.IGNORECASE).strip()
                nombre_target = re.sub(r'\s+(?:para|en|el|la|de|a|este|esta|un|su|hoy|con)$', '', nombre_target, flags=re.IGNORECASE).strip()

            # Si en este mensaje no está el nombre pero dijo "Renovale su plan", inspeccionar el mensaje anterior
            if not nombre_target or nombre_target.lower() in ['su', 'su plan', 'el plan', 'un plan']:
                for m_prev in mensajes_previos:
                    if m_prev.direccion == 'ENTRANTE' and m_prev.texto != mensaje_usuario:
                        m_arranco = re.search(r'^([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)\s+(?:hoy|arranc|abon|pag|es)', m_prev.texto, re.IGNORECASE)
                        if m_arranco:
                            nombre_target = m_arranco.group(1).strip()
                            break

            res = renovar_o_asignar_plan_alumna.invoke({
                "nombre_o_tel_alumna": nombre_target or mensaje_usuario,
                "nombre_o_clases_plan": clases_target
            })
            _guardar_hitl_si_corresponde(conversacion, res, 'renovar_plan', {'nombre_o_clases_plan': clases_target})
            tools_usadas.append('renovar_o_asignar_plan_alumna')
            return res, "agente_direccion", tools_usadas

        # 0b. Consulta de ficha o situación de una alumna
        es_consulta_ficha = (
            any(k in msg_low for k in [
                'ficha de', 'datos de', 'cómo viene', 'como viene',
                'cuántas clases le quedan a', 'cuantas clases le quedan a', 'alumna ',
                'plan tiene', 'qué plan tiene', 'que plan tiene', 'q plan tiene', 'abono tiene',
                'qué abono tiene', 'que abono tiene', 'q abono tiene', 'plan de', 'abono de'
            ]) or
            ('plan' in msg_low and any(k in msg_low for k in ['tiene', 'de', 'quién', 'quien', 'consultar', 'fijate', 'decime'])) or
            ('abono' in msg_low and any(k in msg_low for k in ['tiene', 'de', 'quién', 'quien', 'consultar', 'fijate', 'decime'])) or
            bool(re.search(r'\b(?:qu[eé]|\bq\b)\s+(?:plan|abono)\b', msg_low)) or
            bool(re.search(r'\b(?:plan|abono)\s+(?:tiene|de)\s+[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]', msg_low))
        )
        if es_consulta_ficha:
            m_alumna = re.search(
                r'(?:ficha de|datos de|cómo viene|como viene|clases le quedan a|alumna|(?:qu[eé]|\bq\b)?\s*(?:plan|abono)\s+(?:tiene|de)|plan de|abono de)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:\s+(?:hoy|el|este|esta)|$|[?.,!])',
                mensaje_usuario,
                re.IGNORECASE
            )
            nom = m_alumna.group(1).strip() if m_alumna else ""
            if not nom:
                m_nom_pre = re.search(r'^([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)\s+(?:qu[eé]|\bq\b)?\s*(?:plan|abono)\s+tiene', mensaje_usuario, re.IGNORECASE)
                if m_nom_pre:
                    nom = m_nom_pre.group(1).strip()
            nom = nom or mensaje_usuario
            nom = re.sub(r'^(?:decime|fijate|consultame|porfa|por favor)\s+', '', nom, flags=re.IGNORECASE).strip()
            nom = re.sub(r'\s+(?:para|en|el|la|de|a|este|esta)$', '', nom, flags=re.IGNORECASE).strip()
            res = consultar_alumna_detalle.invoke({"nombre_o_tel": nom})
            _guardar_hitl_si_corresponde(conversacion, res, 'consultar_ficha', {})
            tools_usadas.append('consultar_alumna_detalle')
            return res, "agente_direccion", tools_usadas

        # 0f. Abrir / crear clase nueva extraordinaria y agendar alumna
        if any(k in msg_low for k in [
            'agregar una clase', 'agrega una clase', 'agregá una clase',
            'crear una clase', 'crea una clase', 'creá una clase',
            'abrir una clase', 'abrí una clase', 'abrir clase', 'abrí clase',
            'abrir un turno', 'abrí un turno', 'crear un turno', 'creá un turno',
            'nueva clase', 'nuevo turno'
        ]):
            hora_match = re.search(r'(\d{1,2}(?::\d{2})?(?:\s*hs)?)', msg_low)
            hora_str = hora_match.group(1) if hora_match else "18:00"
            fecha_str = "hoy"
            for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado', 'mañana', 'hoy']:
                if d in msg_low:
                    fecha_str = d
                    break
            
            nom = ""
            m_nom_clase = re.search(
                r'(?:(?:est[eé]\s+)?anotad[oa]\s+(?:a\s+)?|anot(?:ar|[aá]|ale|alo|ala)?\s+a\s+|anotando\s+a\s+|para\s+)([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:\s+(?:el|a\s+las|\d)|$|[?.,!])',
                mensaje_usuario,
                re.IGNORECASE
            )
            if m_nom_clase:
                nom = m_nom_clase.group(1).strip()
                nom = re.sub(r'\s+(?:para|en|el|la|de|a|este|esta)$', '', nom, flags=re.IGNORECASE).strip()
                if nom.lower() in ['que', 'q', 'este', 'esté']:
                    nom = ""

            res = crear_clase_y_agendar_alumna_duena.invoke({
                "fecha_o_dia": fecha_str,
                "hora_str": hora_str,
                "nombre_o_tel_alumna": nom
            })
            _guardar_hitl_si_corresponde(conversacion, res, 'crear_clase_y_agendar', {'fecha_o_dia': fecha_str, 'hora_str': hora_str})
            tools_usadas.append('crear_clase_y_agendar_alumna_duena')
            return res, "agente_direccion", tools_usadas

        # 0c. Anotar / agendar / agregar alumna manualmente en una camilla
        if any(k in msg_low for k in [
            'agendar a', 'agendá a', 'agenda a', 'agendale a', 'agendala a', 'agendalo a',
            'anotar a', 'anotá a', 'anota a', 'anotale a', 'anotala a', 'anotalo a',
            'inscribir a', 'inscribí a', 'inscribi a', 'inscribile a', 'anotame a', 'anotáme a',
            'agregá a', 'agrega a', 'agregar a', 'sumá a', 'suma a', 'sumar a'
        ]) and not ('plan' in msg_low):
            m_anota = re.search(
                r'(?:agend(?:ar|[aá])|anot(?:ar|[aá])|inscrib(?:ir|[ií])|agreg(?:ar|[aá])|sum(?:ar|[aá]))(?:le|la|lo)?\s+a\s+([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:\s+(?:para\s+el|para\s+la|para|en\s+el|en\s+la|en|el|la|este|esta|hoy|mañana|a\s+las|\d)|$|[?.,!])',
                mensaje_usuario,
                re.IGNORECASE
            )
            nom = m_anota.group(1).strip() if m_anota else ""
            nom = re.sub(r'\s+(?:para|en|el|la|de|a|este|esta)$', '', nom, flags=re.IGNORECASE).strip()
            hora_match = re.search(r'(\d{1,2}(?::\d{2})?(?:\s*hs)?)', msg_low)
            hora_str = hora_match.group(1) if hora_match else "18:00"
            fecha_str = "hoy"
            for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado', 'mañana', 'hoy']:
                if d in msg_low:
                    fecha_str = d
                    break
            res = agendar_alumna_en_turno_duena.invoke({
                "nombre_o_tel_alumna": nom,
                "fecha_o_dia": fecha_str,
                "hora_str": hora_str
            })
            _guardar_hitl_si_corresponde(conversacion, res, 'agendar', {'fecha_o_dia': fecha_str, 'hora_str': hora_str})
            tools_usadas.append('agendar_alumna_en_turno_duena')
            return res, "agente_direccion", tools_usadas

        # 0d. Ver agenda o consultar qué alumnas hay en cada clase
        es_consulta_agenda = (
            any(k in msg_low for k in [
                'ver agenda', 'la agenda', 'quiénes vienen', 'quienes vienen',
                'quiénes están', 'quienes estan', 'quiénes asisten', 'quienes asisten',
                'grilla de hoy', 'turnos de hoy', 'cómo viene el día', 'como viene el dia',
                'alumnas hay', 'alumnos hay', 'qué alumnas', 'que alumnas', 'qué alumnos', 'que alumnos'
            ]) or
            re.search(r'\bagenda\b', msg_low)
        )
        if es_consulta_agenda:
            fecha_str = "mañana" if any(k in msg_low for k in ['mañana', 'manana']) else "hoy"
            for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado']:
                if d in msg_low:
                    fecha_str = d
                    break
            hora_match = re.search(r'(\d{1,2}(?::\d{2})?(?:\s*hs)?)', msg_low)
            hora_str = hora_match.group(1) if hora_match else ""
            res = consultar_agenda_completa_dia.invoke({"fecha_o_dia": fecha_str, "hora_str": hora_str})
            tools_usadas.append('consultar_agenda_completa_dia')
            return res, "agente_direccion", tools_usadas

        # 0e. Sacar / desanotar / cancelar clase puntual a una alumna
        if any(k in msg_low for k in [
            'sacá a', 'saca a', 'sacar a', 'sacala a', 'sacale a',
            'desanotá a', 'desanota a', 'desanotar a', 'desanotale a',
            'bajá a', 'baja a', 'bajar a', 'bajala a',
            'cancelale la clase a', 'cancelale el turno a', 'cancelar la clase de', 'cancelale a'
        ]) and not any(k in msg_low for k in [' y poné a', ' y pone a', ' por ']):
            m_saca = re.search(r'(?:sac[aá]|desanot[aá]|baj[aá]|cancel[aá](?:le)?(?:\s+la\s+clase)?)(?:le|la|lo)?\s+(?:a\s+)?([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+?)(?:\s+(?:de\s+la\s+clase|del\s+turno|para\s+el|para|hoy|mañana|el|a\s+las|\d)|$|[?.,!])', mensaje_usuario, re.IGNORECASE)
            nom = m_saca.group(1).strip() if m_saca else ""
            nom = re.sub(r'\s+(?:para|en|el|la|de|a|este|esta)$', '', nom, flags=re.IGNORECASE).strip()
            hora_match = re.search(r'(\d{1,2}(?::\d{2})?(?:\s*hs)?)', msg_low)
            hora_str = hora_match.group(1) if hora_match else ""
            fecha_str = "hoy"
            for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado', 'mañana', 'hoy']:
                if d in msg_low:
                    fecha_str = d
                    break
            res = cancelar_reserva_alumna_duena.invoke({
                "nombre_o_tel_alumna": nom,
                "fecha_o_dia": fecha_str,
                "hora_str": hora_str
            })
            _guardar_hitl_si_corresponde(conversacion, res, 'cancelar', {'fecha_o_dia': fecha_str, 'hora_str': hora_str})
            tools_usadas.append('cancelar_reserva_alumna_duena')
            return res, "agente_direccion", tools_usadas

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

        # 3. Reasignación directa de profesoras
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

        # 5. Análisis de ocupación y clases llenas del mes
        if any(k in msg_low for k in ['clases llenas', 'clase llena', 'porcentaje de clases', 'ocupación del mes', 'ocupacion del mes', 'ocupación mensual', 'ocupacion mensual']):
            from ..tools.reportes_tools import obtener_reporte_ocupacion_mes
            res = obtener_reporte_ocupacion_mes.invoke({"mes_o_fecha": msg_low})
            tools_usadas.append('obtener_reporte_ocupacion_mes')
            return res, "agente_reportes", tools_usadas

        if any(k in msg_low for k in ['ocupacion', 'ocupación', 'consolidar', 'optimizar', 'clases solas', 'poca gente']):
            fecha_str = "mañana" if any(k in msg_low for k in ['mañana', 'manana']) else "hoy"
            res = analizar_optimizacion_turnos_proximos.invoke({"fecha_str": fecha_str})
            tools_usadas.append('analizar_optimizacion_turnos_proximos')
            return res, "optimizador_ocupacion", tools_usadas

        # 6. Vínculos inseparables
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

        # 7. Reportes de facturación / métricas de la dueña
        if any(k in msg_low for k in ['factur', 'ingreso', 'reporte', 'dinero', 'plata', 'mes entero', 'todo el mes', 'del mes', 'balance', 'recaudac', 'no de una semana']):
            es_semanal = ('semana' in msg_low) and not any(m in msg_low for m in ['mes', 'octubre', 'septiembre', 'noviembre', 'no de una semana', 'del mes entero', 'todo el mes'])
            periodo = "semana" if es_semanal else "mes"
            mes_match = ""
            for m in ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']:
                if m in msg_low:
                    mes_match = m
                    break
            res = obtener_reporte_facturacion.invoke({"periodo": periodo, "mes_o_fecha": mes_match})
            tools_usadas.append('obtener_reporte_facturacion')
            return res, "agente_direccion", tools_usadas

        # Fallback exclusivo para la Dueña: NUNCA caer en la lógica de clientas ni ofrecerle planes a ella
        return (
            "Decime Deby ✦, ¿en qué te puedo ayudar hoy con el estudio? Puedo pasarte el reporte de facturación (mensual o semanal), la cantidad de alumnas, la ocupación de camillas, consultar el plan de una alumna o gestionar turnos y abonos.",
            "agente_direccion",
            []
        )

    # --- CONSULTAS DE PROFESORAS ---
    if rol == 'PROFESOR':
        if any(k in msg_low for k in ['mis clases', 'que clases tengo', 'horario']):
            res = consultar_mis_clases_profesor.invoke({"profesor_usuario_id": usuario_id})
            tools_usadas.append('consultar_mis_clases_profesor')
            return res, "agente_profesores", tools_usadas

    # --- CONSULTAS DE ALUMNAS Y CLIENTAS (CONVERSACIONAL Y CÁLIDO) ---

    # 1. Confirmación de reserva / intención de anotarse tras ver turnos
    if ('turnos disponibles' in ultimo_mensaje_bot or 'horarios disponibles' in ultimo_mensaje_bot) and any(k in msg_low for k in ['anotame', 'anotáme', 'el de las', 'a las', 'dale', 'reservame', 'guardame']):
        hora_match = re.search(r'(\d{1,2}(?::\d{2})?)', msg_low)
        hora_deseada = hora_match.group(1) if hora_match else ""
        
        # Validar créditos antes de intentar
        try:
            from plugins.membresias.backend.models import Suscripcion
            sub = Suscripcion.objects.filter(usuario_id=usuario_id, estado__in=['ACTIVO', 'AGOTADO']).first()
        except Exception:
            sub = None

        if sub and sub.clases_restantes <= 0:
            return (
                f"{saludo_base}Me fijé para anotarte, pero veo que ya tenés agendadas todas las clases de tu abono de este mes, por lo que no te quedan créditos libres para reservar otra clase por ahora.\n\n"
                f"Si querés sumar una clase individual extra o renovar tu abono para el próximo ciclo, avisame y lo coordinamos juntas con todo gusto 🌸.",
                "agente_turnos_simulado",
                []
            )

        if hora_deseada and usuario_id:
            res_reserva = reservar_camilla_turno.invoke({
                "usuario_id": usuario_id,
                "fecha_o_dia": "mañana" if "mañana" in ultimo_mensaje_bot else "hoy",
                "hora_str": hora_deseada
            })
            tools_usadas.append('reservar_camilla_turno')
            return f"¡Listo {nombre_display}! ✦ {res_reserva}", "agente_turnos_simulado", tools_usadas

    # 1.5 Consulta de MIS clases / Próxima clase de la alumna ("cuándo tengo clases", "cuándo es mi próxima clase", "qué clase me toca")
    es_consulta_mis_clases = any(k in msg_low for k in [
        'cuando tengo clase', 'cuándo tengo clase', 'cuando tengo clases', 'cuándo tengo clases',
        'que clase me toca', 'qué clase me toca', 'que clases me tocan', 'qué clases me tocan',
        'mi proxima clase', 'mi próxima clase', 'proxima clase', 'próxima clase',
        'mis clases', 'mis turnos', 'mis horarios', 'a que hora tengo', 'a qué hora tengo',
        'a que hora voy', 'a qué hora voy', 'cuando voy', 'cuándo voy', 'cuando vengo', 'cuándo vengo',
        'estoy anotada', 'estoy anotado', 'que dia voy', 'qué día voy', 'tengo clase hoy',
        'tengo clase manana', 'tengo clase mañana', 'tengo clase el', 'tengo clase este',
        'mis reservas', 'mi reserva', 'cuando me toca', 'cuándo me toca'
    ]) or (
        ('cuando' in msg_low or 'cuándo' in msg_low or 'a que hora' in msg_low or 'a qué hora' in msg_low)
        and ('tengo' in msg_low or 'me toca' in msg_low or 'voy' in msg_low or 'es mi' in msg_low or 'estoy' in msg_low)
    )
    if es_consulta_mis_clases:
        if not usuario_id and conversacion.usuario:
            usuario_id = str(conversacion.usuario.id)
        if not usuario_id and conversacion.telefono:
            from ..tools.gestion_tools import buscar_usuario_por_telefono
            u_found = buscar_usuario_por_telefono(conversacion.telefono)
            if u_found:
                usuario_id = str(u_found.id)
        res = consultar_mis_reservas_alumna.invoke({"usuario_id": usuario_id})
        tools_usadas.append('consultar_mis_reservas_alumna')
        return res, "agente_turnos_simulado", tools_usadas

    # 2. Consulta de turnos / horarios / disponibilidad
    if any(k in msg_low for k in ['turno', 'horario', 'disponib', 'clase', 'hoy', 'mañana', 'lugar', 'camilla', 'cuando puedo ir']):
        fecha = 'mañana' if any(k in msg_low for k in ['mañana', 'manana']) else 'hoy'
        for d in ['lunes', 'martes', 'miercoles', 'miércoles', 'jueves', 'viernes', 'sabado', 'sábado']:
            if d in msg_low:
                fecha = d
                break

        res = consultar_turnos_disponibles.invoke({"fecha_str": fecha})
        tools_usadas.append('consultar_turnos_disponibles')

        if "no hay turnos" in res.lower() or "sin camillas" in res.lower():
            return (
                f"{saludo_base}Me fijé en la grilla para esa fecha pero por el momento tenemos todas las camillas completas.\n\n"
                f"Si querés, me puedo fijar para el día siguiente o para otro horario que te quede cómodo, ¿te parece?",
                "agente_turnos_simulado",
                tools_usadas
            )

        return (
            f"{saludo_base}Con mucho gusto, me fijé en el sistema y tenemos estos lugares disponibles en camilla Reformer:\n\n"
            f"{res}\n\n"
            f"¿Te queda bien alguno de estos horarios? Decime cuál preferís y ya te aseguro tu camilla ✦.",
            "agente_turnos_simulado",
            tools_usadas
        )

    # 3. Consulta de plan / saldo / créditos restantes
    if any(k in msg_low for k in ['plan', 'credito', 'crédito', 'clases que me quedan', 'cuantas clases', 'cuántas clases', 'vence', 'vencimiento', 'mi abono']):
        if usuario_id:
            try:
                from plugins.membresias.backend.models import Suscripcion
                sub = Suscripcion.objects.filter(
                    usuario_id=usuario_id,
                    estado__in=['ACTIVO', 'AGOTADO']
                ).select_related('plan').order_by('-fecha_inicio').first()
            except Exception:
                sub = None

            if sub:
                tools_usadas.append('consultar_estado_plan_alumna')
                venc_str = sub.fecha_vencimiento.strftime('%d/%m/%Y')
                
                if sub.clases_restantes == 0:
                    return (
                        f"{saludo_base}Estuve mirando en tu cuenta y veo que tenés el {sub.plan.nombre}, "
                        f"pero ya tenés todas las clases de este mes agendadas, por lo que no te quedan créditos libres para reservar otro turno por ahora.\n\n"
                        f"Si querés sumar alguna clase extra o renovar tu abono para el próximo mes, avisame y lo vemos juntas con mucho gusto 🌸.",
                        "agente_finanzas_simulado",
                        tools_usadas
                    )
                else:
                    return (
                        f"{saludo_base}Te cuento que tenés disponibles {sub.clases_restantes} clase(s) "
                        f"de tu {sub.plan.nombre} para aprovechar hasta el {venc_str} ✦.\n\n"
                        f"¿Te gustaría que te busque lugar en algún día y horario para agendar tu clase?",
                        "agente_finanzas_simulado",
                        tools_usadas
                    )

        # Si no está identificada o no tiene plan
        planes = obtener_planes_y_precios.invoke({})
        tools_usadas.append('obtener_planes_y_precios')
        return (
            f"{saludo_base}Por el momento no veo ningún abono activo a tu nombre en el sistema. "
            f"Te comparto los planes que tenemos disponibles para sumarte:\n\n{planes}\n\n"
            f"¿Te gustaría que te cuente cómo es la primera clase o querés consultar horarios?",
            "agente_finanzas_simulado",
            tools_usadas
        )

    # 4. Consulta de precios / valores / transferencias
    if any(k in msg_low for k in ['precio', 'cuanto sale', 'cuánto sale', 'costo', 'pagar', 'transfer', 'alias', 'cbu', 'datos']):
        planes = obtener_planes_y_precios.invoke({})
        datos = obtener_datos_transferencia_estudio.invoke({})
        tools_usadas.extend(['obtener_planes_y_precios', 'obtener_datos_transferencia_estudio'])
        return (
            f"{saludo_base}Con mucho gusto te paso la información de nuestros planes y los datos para transferir:\n\n"
            f"{planes}\n\n{datos}\n\n"
            f"El plan más elegido por nuestras alumnas es el de 8 clases mensuales (2 veces por semana) para mantener la constancia y sentir la espalda liviana 🌸. "
            f"¿Querés que te guarde lugar en algún horario para empezar?",
            "agente_finanzas_simulado",
            tools_usadas
        )

    # 5. Dudas sobre la ubicación / dirección del estudio
    if any(k in msg_low for k in ['donde estan', 'dónde están', 'donde queda', 'dónde queda', 'direccion', 'dirección', 'ubicacion', 'ubicación']):
        return (
            f"{saludo_base}Nuestro estudio boutique está ubicado en Gral. Guido 1573, Ramos Mejía ✦.\n\n"
            f"Es un espacio íntimo y cálido con grupos reducidos de hasta 3 camillas Reformer por turno, para que tengas una práctica guiada y súper cuidada.\n\n"
            f"¿Querías pasar a conocer el lugar o te gustaría ver turnos disponibles?",
            "asistente_recepcionista",
            []
        )

    # 6. Dudas sobre el método / principiantes / dolor de espalda / edad
    if any(k in msg_low for k in ['duele', 'espalda', 'edad', 'principiante', 'nunca hice', 'como son las clases', 'cómo son las clases']):
        return (
            f"{saludo_base}¡No te preocupes en absoluto! En Violett las clases son súper personalizadas (máximo 3 alumnas por turno) y nuestras profesoras están formadas en anatomía y cuidado postural 🌸.\n\n"
            f"Cada clase dura 60 minutos: 55 minutos de trabajo suave y controlado en Reformer para aliviar tensiones, y 5 minutos finales de masajes de descompresión asistido.\n\n"
            f"Nos adaptamos al ritmo de tu cuerpo desde la primera clase. ¿Te gustaría que nos fijemos algún horario para que vengas a probar?",
            "asistente_recepcionista",
            []
        )

    # 7. Agradecimientos, confirmaciones amables o despedidas
    if any(k in msg_low for k in ['gracias', 'muchas gracias', 'genial', 'buenisimo', 'buenísimo', 'perfecto', 'dale gracias', 'chau', 'hasta luego']):
        return (
            f"¡Por nada, {nombre_display}! ✦ Cualquier otra consulta que tengas sobre tus clases o el estudio, escribime cuando quieras que acá estoy para acompañarte.\n\n"
            f"¡Que tengas un hermoso día! 🌸",
            "asistente_recepcionista",
            []
        )

    # 8. Saludos o mensajes breves de seguimiento
    if ya_saludo_reciente:
        if rol == 'DUENA':
            return (
                f"Decime, Deby ✦, ¿en qué te puedo ayudar hoy con el estudio? Puedo pasarte el reporte de facturación (mensual o semanal), ver la ocupación de camillas de hoy o ayudarte con los horarios y comprobantes.",
                "agente_direccion",
                []
            )
        if 'turnos disponibles' in ultimo_mensaje_bot or 'horarios disponibles' in ultimo_mensaje_bot:
            return (
                f"Decime, {nombre_display}, ¿te gustaría que te reserve alguna camilla en los horarios que vimos, o preferís que busquemos para otro día?",
                "asistente_recepcionista",
                []
            )
        if 'en qué te puedo orientar hoy' in ultimo_mensaje_bot:
            return (
                f"Decime {nombre_display}, ¿en qué puedo ayudarte hoy? Si querés consultar turnos libres, el estado de tu abono o precios de los planes, avisame con confianza 🌸.",
                "asistente_recepcionista",
                []
            )
        return (
            f"Decime, {nombre_display}, ¿en qué te puedo orientar hoy? ¿Querías consultar algún horario en especial o tenías alguna duda sobre los planes?",
            "asistente_recepcionista",
            []
        )

    # 9. Saludo inicial por primera vez
    if rol == 'DUENA':
        return (
            f"¡Hola Deby! ✦ ¿En qué te puedo ayudar hoy con la gestión del estudio? Puedo prepararte el reporte de facturación (mensual o semanal), el estado de ocupación de las camillas para hoy, o asistirte con la grilla y comprobantes.",
            "agente_direccion",
            []
        )

    saludo_inicial = f"¡Hola {nombre_display}! ✦ " if nombre_display else "¡Hola! ✦ "
    return (
        f"{saludo_inicial}Bienvenida a Violett Pilates. Soy la asistente del estudio.\n\n"
        f"Puedo ayudarte a consultar turnos disponibles en Reformer, reservar tu camilla o brindarte información de nuestros abonos mensuales.\n\n"
        f"¿En qué te puedo acompañar hoy?",
        "asistente_recepcionista",
        tools_usadas
    )
