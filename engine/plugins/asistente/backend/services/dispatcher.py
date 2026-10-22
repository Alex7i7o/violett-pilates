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
        # Buscamos por coincidencia de ultimos 8 digitos del telefono
        ultimos_digitos = clean_phone[-8:]
        usuario = Usuario.objects.filter(telefono__icontains=ultimos_digitos).first()
        if usuario:
            conversacion.usuario = usuario

    # 3. Detectar rol (con coincidencia robusta para celular argentino de la dueña)
    ultimos_duena = telefono_duena[-8:] if len(telefono_duena) >= 8 else telefono_duena
    if clean_phone and ultimos_duena and clean_phone.endswith(ultimos_duena):
        conversacion.rol_detectado = 'DUENA'
    elif conversacion.usuario:
        is_profesor = getattr(conversacion.usuario, 'is_profesor', False) or str(getattr(conversacion.usuario, 'rol', '')).upper() == 'PROFESOR'
        if is_profesor:
            conversacion.rol_detectado = 'PROFESOR'
        else:
            conversacion.rol_detectado = 'ALUMNA'
    else:
        conversacion.rol_detectado = 'PROSPECTO'

    conversacion.save()

    # 4. Registrar log del mensaje entrante
    es_audio = data.get('es_audio', False)
    texto_log = f"🎤 [Audio]: {text}" if es_audio else text
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
            mensaje_usuario=text
        )
    except Exception as e:
        print(f"[ASISTENTE ERROR GRAFO] Excepción para {clean_phone}: {e}", flush=True)
        logger.error(f"[ASISTENTE ERROR] Excepción ejecutando LangGraph para {clean_phone}: {e}", exc_info=True)
        respuesta_texto = "¡Hola! ✦ Disculpá, estoy experimentando una breve interrupción momentánea. En unos minutos vuelvo a estar disponible."
        agente_responsable = "fallback_error"
        tools_usadas = []

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
