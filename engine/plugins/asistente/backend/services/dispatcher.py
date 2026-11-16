import logging
import threading
from django.utils import timezone
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

def procesar_mensaje_entrante_async(data: dict):
    """
    Despacha el procesamiento del mensaje en un thread secundario
    para que la vista webhook devuelva HTTP 200 a Meta inmediatamente (<500ms).
    """
    thread = threading.Thread(target=_ejecutar_ciclo_agente, args=(data,), daemon=True)
    thread.start()

def _ejecutar_ciclo_agente(data: dict):
    from ..models import ConversacionWhatsApp, MensajeWhatsAppLog
    from core.models import Usuario

    phone = data.get('phone')
    text = data.get('text', '').strip()
    if not phone or not text:
        return

    config = get_asistente_config()
    telefono_duena = config.get('telefono_duena', '').replace('+', '').replace(' ', '').replace('-', '')
    clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
    print(f"[ASISTENTE CICLO INICIADO] Mensaje de {clean_phone}: '{text}'", flush=True)

    # 1. Obtener o crear Conversacion
    conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)

    # 2. Vincular usuario si aun no esta vinculado
    if not conversacion.usuario:
        from ..tools.gestion_tools import buscar_usuario_por_telefono
        usuario = buscar_usuario_por_telefono(clean_phone)
        if usuario:
            conversacion.usuario = usuario

    # 3. Detectar rol (reconocimiento automático de Débora y miembros del Staff con permisos de dirección)
    from ..config_loader import es_telefono_staff_o_duena
    if es_telefono_staff_o_duena(clean_phone):
        conversacion.rol_detectado = 'DUENA'
    elif conversacion.usuario:
        is_profesor = getattr(conversacion.usuario, 'is_profesor', False) or str(getattr(conversacion.usuario, 'rol', '')).upper() == 'PROFESOR'
        if is_profesor:
            conversacion.rol_detectado = 'PROFESOR'
        else:
            conversacion.rol_detectado = 'ALUMNA'
    else:
        conversacion.rol_detectado = 'PROSPECTO'

    # 3.1 Recuperar contexto si la usuaria respondió citando un mensaje de WhatsApp
    raw_msg = data.get('raw_msg', {})
    quoted_wamid = data.get('quoted_wamid') or (raw_msg.get('context', {}).get('id') if isinstance(raw_msg, dict) else None)
    texto_citado = None
    if quoted_wamid:
        wamid_map = conversacion.metadata.get('sent_wamid_map', {})
        texto_citado = wamid_map.get(quoted_wamid)

    # 3.2 Si no citó explícitamente pero es Débora/Staff respondiendo a una alerta reciente de agenda
    if not texto_citado and conversacion.rol_detectado == 'DUENA':
        import datetime
        hace_20m = timezone.now() - datetime.timedelta(minutes=20)
        ultimo_aviso = conversacion.mensajes.filter(
            direccion='SALIENTE',
            created_at__gte=hace_20m
        ).order_by('-created_at').first()
        if ultimo_aviso and any(k in ultimo_aviso.texto.lower() for k in ['alerta', 'solo 1 alumna', 'aviso dirección', 'camillas libres']):
            text_low = text.lower()
            if any(k in text_low for k in ['ese horario', 'esa clase', 'agrega a', 'agregale a', 'agrégale a', 'anota a', 'anotá a', 'pone como profesora', 'poné como profesora', 'cancelala', 'cancelá esa', 'hola no', 'y esta esta']):
                texto_citado = ultimo_aviso.texto

    texto_para_agente = f'[En respuesta a tu aviso anterior: "{texto_citado}"]\n{text}' if texto_citado else text

    conversacion.save()

    # 4. Registrar log del mensaje entrante
    es_audio = data.get('es_audio', False)
    texto_base = f"🎤 [Audio]: {text}" if es_audio else text
    if texto_citado:
        primera_linea = texto_citado.split('\n')[0][:80]
        texto_log = f"↩️ [En respuesta a: \"{primera_linea}...\"]\n{texto_base}"
    else:
        texto_log = texto_base

    MensajeWhatsAppLog.objects.create(
        conversacion=conversacion,
        direccion='ENTRANTE',
        agente_responsable='usuario',
        texto=texto_log
    )

    # 5. Si la conversación está pausada para atención humana, no responder automáticamente
    if conversacion.estado == 'ESPERANDO_HUMANO':
        logger.info(f"[ASISTENTE] Conversación con {clean_phone} en ESPERANDO_HUMANO. No se genera respuesta automática.")
        return

    # 6. Ejecutar Orquestador LangGraph (o simulador de tools)
    try:
        from ..graph.runner import ejecutar_grafo_asistente
        respuesta_texto, agente_responsable, tools_usadas = ejecutar_grafo_asistente(
            conversacion=conversacion,
            mensaje_usuario=texto_para_agente
        )
    except Exception as e:
        print(f"[ASISTENTE ERROR GRAFO] Excepción para {clean_phone}: {e}", flush=True)
        logger.error(f"[ASISTENTE ERROR] Excepción ejecutando LangGraph para {clean_phone}: {e}", exc_info=True)
        from .debugger_service import registrar_y_diagnosticar_error
        respuesta_texto, _ = registrar_y_diagnosticar_error(
            conversacion=conversacion,
            mensaje_usuario=text,
            excepcion=e,
            agente_responsable="fallback_error"
        )
        agente_responsable = "centinela_debugger"
        tools_usadas = []

    # Sanitizar formato nativo de WhatsApp (eliminar ###, convertir tablas y ** a *)
    try:
        from .formatter import sanitizar_para_whatsapp
        respuesta_texto = sanitizar_para_whatsapp(respuesta_texto)
    except Exception as e:
        logger.warning(f"[ASISTENTE] Error sanitizando mensaje para WhatsApp: {e}")

    # 7. Registrar mensaje saliente en el log
    MensajeWhatsAppLog.objects.create(
        conversacion=conversacion,
        direccion='SALIENTE',
        agente_responsable=agente_responsable,
        texto=respuesta_texto,
        tools_ejecutadas=tools_usadas
    )

    # 8. Despachar a WhatsApp
    print(f"[ASISTENTE DESPACHANDO RESPUESTA] De: {agente_responsable} -> A: {clean_phone} -> '{respuesta_texto[:60]}...'", flush=True)
    client = WhatsAppClient()
    client.send_text_message(clean_phone, respuesta_texto)
    logger.info(f"[ASISTENTE] Mensaje respondido a {clean_phone} por {agente_responsable}: {respuesta_texto[:60]}...")
