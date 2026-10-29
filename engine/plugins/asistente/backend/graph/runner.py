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
        # Usamos únicamente el primer nombre para máxima calidez humana
        nombre_user = conversacion.usuario.nombre.strip() if conversacion.usuario.nombre else ""
        usuario_id = str(conversacion.usuario.id)

    # 1. Modo Simulación si no hay API Key configurada
    if not anthropic_key and not openai_key and not groq_key:
        logger.info("[ASISTENTE SIMULADOR] Ni ANTHROPIC_API_KEY, ni OPENAI_API_KEY ni GROQ_API_KEY configuradas. Ejecutando respuesta conversacional inteligente basada en reglas.")
        return _ejecutar_modo_simulacion(conversacion, mensaje_usuario, usuario_id, nombre_user)

    # 2. Modo Orquestador Multi-Agente con LangGraph
    try:
        # Cargar historial previo de la conversación excluyendo el mensaje entrante recién creado en dispatcher
        mensajes_db = list(conversacion.mensajes.order_by('-created_at')[1:9])
        historial_langchain = []
        for m in reversed(mensajes_db):
            if m.direccion == 'ENTRANTE':
                # Limpiar prefijo [Audio] para fluidez conversacional
                txt = m.texto.replace("🎤 [Audio]: ", "").strip()
                historial_langchain.append(HumanMessage(content=txt))
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
        print(f"[ASISTENTE MULTI-AGENTE ERROR CRITICO] Fallback a simulador por error: {e}", flush=True)
        logger.error(f"[ASISTENTE MULTI-AGENTE ERROR] Fallback a simulador conversacional por error: {e}", exc_info=True)
        return _ejecutar_modo_simulacion(conversacion, mensaje_usuario, usuario_id, nombre_user)


def _ejecutar_modo_simulacion(conversacion, mensaje_usuario: str, usuario_id: str, nombre_user: str) -> Tuple[str, str, List[str]]:
    """
    Modo simulador conversacional inteligente cuando no hay API Key o falla el proveedor LLM.
    Diseñado especialmente con alta empatía, voseo cariñoso, memoria del historial y trato cálido para personas adultas.
    """
    msg_low = mensaje_usuario.lower().strip()
    tools_usadas = []
    rol = conversacion.rol_detectado

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

    es_consulta_facturacion = any(k in msg_low for k in [
        'factur', 'ingreso', 'reporte de facturacion', 'reporte de facturación',
        'cuanta plata', 'cuánta plata', 'balance del mes', 'balance de la semana',
        'recaudacion', 'recaudación', 'ganancias'
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

        # 5. Análisis de ocupación y consolidación de horarios
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
        if 'turnos disponibles' in ultimo_mensaje_bot or 'horarios disponibles' in ultimo_mensaje_bot:
            return (
                f"Decime, {nombre_display}, ¿te gustaría que te reserve alguna camilla en los horarios que vimos, o preferís que busquemos para otro día?",
                "asistente_recepcionista",
                []
            )
        return (
            f"Decime, {nombre_display}, ¿en qué te puedo orientar hoy? ¿Querías consultar algún horario en especial o tenías alguna duda sobre los planes?",
            "asistente_recepcionista",
            []
        )

    # 9. Saludo inicial por primera vez
    saludo_inicial = f"¡Hola {nombre_display}! ✦ " if nombre_display else "¡Hola! ✦ "
    return (
        f"{saludo_inicial}Bienvenida a Violett Pilates. Soy la asistente del estudio.\n\n"
        f"Puedo ayudarte a consultar turnos disponibles en Reformer, reservar tu camilla o brindarte información de nuestros abonos mensuales.\n\n"
        f"¿En qué te puedo acompañar hoy?",
        "asistente_recepcionista",
        tools_usadas
    )
