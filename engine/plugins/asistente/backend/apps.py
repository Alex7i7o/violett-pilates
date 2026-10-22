from django.apps import AppConfig
import sys
import logging

logger = logging.getLogger(__name__)

def run_yield_optimizer_job():
    from django.core.management import call_command
    try:
        call_command("optimizar_ocupacion_proactivo")
    except Exception as e:
        logger.error(f"[ASISTENTE YIELD JOB ERROR] {e}")

def run_recordatorios_proactivos_job():
    from django.core.management import call_command
    try:
        call_command("enviar_recordatorios_proactivos")
    except Exception as e:
        logger.error(f"[ASISTENTE RECORDATORIOS JOB ERROR] {e}")

def run_cancelar_clases_bajo_cupo_job():
    from django.core.management import call_command
    try:
        call_command("cancelar_clases_bajo_cupo")
    except Exception as e:
        logger.error(f"[ASISTENTE CANCELAR CLASES BAJO CUPO ERROR] {e}")

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

        def on_whatsapp_imagen(data, **kwargs):
            try:
                import threading
                from .services.vision_service import procesar_comprobante_imagen
                phone = data.get('phone')
                image_id = data.get('image_id')
                caption = data.get('caption', '')
                if phone and image_id:
                    threading.Thread(target=procesar_comprobante_imagen, args=(phone, image_id, caption), daemon=True).start()
            except Exception as e:
                logger.error(f"[ASISTENTE ERROR] Error despachando imagen entrante: {e}")
            return data

        def on_whatsapp_audio(data, **kwargs):
            try:
                import threading
                from .services.audio_service import procesar_audio_entrante_async
                phone = data.get('phone')
                audio_id = data.get('audio_id')
                mime_type = data.get('mime_type', 'audio/ogg')
                if phone and audio_id:
                    threading.Thread(
                        target=procesar_audio_entrante_async,
                        args=(phone, audio_id, mime_type),
                        daemon=True
                    ).start()
            except Exception as e:
                logger.error(f"[ASISTENTE ERROR] Error despachando audio entrante: {e}")
            return data

        registry.register('whatsapp_mensaje_recibido', on_whatsapp_mensaje)
        registry.register('whatsapp_imagen_recibida', on_whatsapp_imagen)
        registry.register('whatsapp_audio_recibido', on_whatsapp_audio)
        logger.info("[ASISTENTE IA] Hooks 'whatsapp_mensaje_recibido', 'whatsapp_imagen_recibida' y 'whatsapp_audio_recibido' registrados.")

        # Iniciar Scheduler proactivo en background si no es un comando de migración/shell
        if not any(cmd in arg for arg in sys.argv for cmd in ['makemigrations', 'migrate', 'collectstatic', 'shell', 'test']):
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from django_apscheduler.jobstores import DjangoJobStore

                scheduler = BackgroundScheduler()
                scheduler.add_jobstore(DjangoJobStore(), "default")

                scheduler.add_job(
                    run_yield_optimizer_job,
                    trigger="interval",
                    minutes=30,
                    id="asistente_yield_optimizer_job",
                    replace_existing=True
                )
                scheduler.add_job(
                    run_recordatorios_proactivos_job,
                    trigger="interval",
                    minutes=15,
                    id="asistente_recordatorios_proactivos_job",
                    replace_existing=True
                )
                scheduler.add_job(
                    run_cancelar_clases_bajo_cupo_job,
                    trigger="interval",
                    minutes=60,
                    id="asistente_cancelar_clases_bajo_cupo_job",
                    replace_existing=True
                )
                scheduler.start()
                logger.info("[ASISTENTE IA] Scheduler proactivo iniciado: ocupación (cada 30 min), recordatorios (cada 15 min), cancelación bajo cupo (cada 60 min).")
            except Exception as e:
                logger.warning(f"[ASISTENTE IA] Scheduler proactivo no iniciado: {e}")
