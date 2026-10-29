import os
import io
import logging
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..models import ConversacionWhatsApp, MensajeWhatsAppLog
from .dispatcher import _ejecutar_ciclo_agente

logger = logging.getLogger(__name__)

def procesar_audio_entrante_async(phone: str, audio_id: str, mime_type: str = "audio/ogg"):
    """
    Descarga el audio de voz de WhatsApp desde Meta Cloud API y lo transcribe
    utilizando Whisper (Groq whisper-large-v3-turbo o OpenAI whisper-1).
    Luego inyecta el texto resultante en el flujo multi-agente de LangGraph.
    """
    clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
    conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)

    client = WhatsAppClient()
    audio_bytes = client.download_media_bytes(audio_id)

    groq_key = os.environ.get('GROQ_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')

    # 1. Si no se pudieron descargar los bytes del audio
    if not audio_bytes:
        logger.warning(f"[ASISTENTE AUDIO] No se pudieron descargar bytes de audio {audio_id} para {clean_phone}")
        client.send_text_message(
            clean_phone,
            "¡Hola! ✦ Disculpá, no logré descargar tu mensaje de audio. ¿Podrías reenviarlo o escribirme tu consulta por mensaje de texto? ¡Muchas gracias!"
        )
        return

    # 2. Si no hay API key para Whisper configurada en el servidor
    if not groq_key and not openai_key:
        logger.warning(f"[ASISTENTE AUDIO] Ni GROQ_API_KEY ni OPENAI_API_KEY configuradas para transcripción de audio en {clean_phone}.")
        client.send_text_message(
            clean_phone,
            "¡Hola! ✦ Recibí tu audio, pero en este momento no tengo activo el transcriptor de voz en el sistema. ¿Podrías escribirme tu consulta por acá en texto así te respondo enseguida? ¡Muchas gracias!"
        )
        return

    # 3. Transcripción con Groq Whisper (Ultra rápido, ~300ms)
    texto_transcrito = ""
    proveedor_usado = ""

    if groq_key:
        try:
            from groq import Groq
            groq_client = Groq(api_key=groq_key)
            model_stt = os.environ.get('GROQ_AUDIO_MODEL', 'whisper-large-v3-turbo')
            
            file_tuple = ("audio.ogg", audio_bytes, mime_type or "audio/ogg")
            
            transcription = groq_client.audio.transcriptions.create(
                file=file_tuple,
                model=model_stt,
                language="es",
                response_format="text"
            )
            texto_transcrito = str(transcription).strip()
            proveedor_usado = f"groq ({model_stt})"
            logger.info(f"[ASISTENTE AUDIO] Groq transcribió audio de {clean_phone}: '{texto_transcrito[:80]}...'")
        except Exception as e:
            logger.error(f"[ASISTENTE AUDIO] Error en transcripción con Groq: {e}", exc_info=True)

    # 4. Fallback a OpenAI Whisper si Groq falla o no está configurado
    if not texto_transcrito and openai_key:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=openai_key)
            file_tuple = ("audio.ogg", audio_bytes, mime_type or "audio/ogg")
            
            res = openai_client.audio.transcriptions.create(
                file=file_tuple,
                model="whisper-1",
                language="es"
            )
            texto_transcrito = res.text.strip() if hasattr(res, 'text') else str(res).strip()
            proveedor_usado = "openai (whisper-1)"
            logger.info(f"[ASISTENTE AUDIO] OpenAI transcribió audio de {clean_phone}: '{texto_transcrito[:80]}...'")
        except Exception as e:
            logger.error(f"[ASISTENTE AUDIO] Error en transcripción con OpenAI: {e}", exc_info=True)

    if not texto_transcrito:
        client.send_text_message(
            clean_phone,
            "¡Hola! ✦ Disculpá, no logré escuchar con claridad tu mensaje de audio. ¿Podrías reenviarlo o escribirme tu consulta en texto? ¡Muchas gracias!"
        )
        return

    # 5. Procesar el texto transcrito con el agente
    _atender_audio_transcrito(conversacion, clean_phone, texto_transcrito, proveedor=proveedor_usado)


def _atender_audio_transcrito(conversacion, clean_phone: str, texto_transcrito: str, proveedor: str = "stt"):
    """
    Registra el audio transcrito y ejecuta el ciclo conversacional del agente.
    """
    logger.info(f"[ASISTENTE AUDIO] Audio procesado ({proveedor}) para {clean_phone}: '{texto_transcrito}'")
    
    # Delegamos al ciclo de agentes pasando el texto como mensaje entrante normal
    _ejecutar_ciclo_agente({
        'phone': clean_phone,
        'text': texto_transcrito,
        'es_audio': True
    })
