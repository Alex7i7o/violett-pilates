from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class AsistenteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.asistente.backend'
    label = 'asistente'

    def ready(self):
        from backend_core.hooks import registry
        
        def on_whatsapp_mensaje(data, **kwargs):
            try:
                from .services.dispatcher import procesar_mensaje_entrante_async
                procesar_mensaje_entrante_async(data)
            except Exception as e:
                logger.error(f"[ASISTENTE ERROR] Error despachando mensaje entrante: {e}")
            return data

        registry.register('whatsapp_mensaje_recibido', on_whatsapp_mensaje)
        logger.info("[ASISTENTE IA] Hook 'whatsapp_mensaje_recibido' registrado exitosamente.")
