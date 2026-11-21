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

def run_notificar_profesores_nocturno_job():
    from django.core.management import call_command
    try:
        call_command("notificar_profesores_agenda_diaria")
    except Exception as e:
        logger.error(f"[ASISTENTE NOTIFICAR PROFESORES NOCTURNO ERROR] {e}")

def run_notificar_clases_una_alumna_job():
    from django.core.management import call_command
    try:
        call_command("notificar_clases_una_alumna")
    except Exception as e:
        logger.error(f"[ASISTENTE NOTIFICAR CLASES 1 ALUMNA ERROR] {e}")

def run_solicitar_asistencia_profesores_job():
    from django.core.management import call_command
    try:
        call_command("solicitar_asistencia_profesores")
    except Exception as e:
        logger.error(f"[ASISTENTE SOLICITAR ASISTENCIA PROFESORES ERROR] {e}")

def run_alertar_vencimiento_abonos_job():
    from django.core.management import call_command
    try:
        call_command("alertar_vencimiento_abonos")
    except Exception as e:
        logger.error(f"[ASISTENTE ALERTA VENCIMIENTO ABONOS ERROR] {e}")

def run_resumen_diario_duena_job():
    from django.core.management import call_command
    try:
        call_command("enviar_resumen_diario_duena")
    except Exception as e:
        logger.error(f"[ASISTENTE RESUMEN DIARIO DUENA ERROR] {e}")

def run_feedback_primera_clase_job():
    from django.core.management import call_command
    try:
        call_command("solicitar_feedback_primera_clase")
    except Exception as e:
        logger.error(f"[ASISTENTE FEEDBACK PRIMERA CLASE ERROR] {e}")

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
                quoted_wamid = data.get('quoted_wamid')
                if phone and image_id:
                    threading.Thread(
                        target=procesar_comprobante_imagen,
                        args=(phone, image_id, caption, quoted_wamid),
                        daemon=True
                    ).start()
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

        def on_reserva_cancelada_check_cupo(data, **kwargs):
            try:
                reserva = data
                if reserva and getattr(reserva, 'turno', None):
                    from .services.notificaciones_duena import notificar_duena_clase_con_una_alumna
                    alumna = getattr(reserva, 'usuario', None)
                    notificar_duena_clase_con_una_alumna(reserva.turno, motivo='cancelacion', alumna_cancelada=alumna)
            except Exception as e:
                logger.error(f"[ALERTA CUPO DUENA ERROR] {e}")
            return data

        registry.register('reserva_cancelada_a_tiempo', on_reserva_cancelada_check_cupo)
        registry.register('reserva_cancelada_tardia', on_reserva_cancelada_check_cupo)
        logger.info("[ASISTENTE IA] Hooks de mensajería y alerta de cupo a dueña registrados.")

        # Iniciar Scheduler proactivo en background si no es un comando de migración/shell/check
        if not any(cmd in arg for arg in sys.argv for cmd in ['makemigrations', 'migrate', 'collectstatic', 'shell', 'test', 'check']):
            # En entornos multi-worker (como Gunicorn con 3 workers), garantizar que SOLO 1 worker inicie el scheduler
            try:
                import socket
                _scheduler_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                _scheduler_lock_socket.bind(('127.0.0.1', 47832))
                self._lock_socket = _scheduler_lock_socket
            except (socket.error, OSError):
                logger.info("[ASISTENTE IA] Scheduler ya activo en otro worker de Gunicorn. Omitiendo instancia duplicada.")
                return

            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from django_apscheduler.jobstores import DjangoJobStore
                from django.conf import settings

                scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
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
                scheduler.add_job(
                    run_notificar_profesores_nocturno_job,
                    trigger="cron",
                    hour=21,
                    minute=0,
                    id="asistente_notificar_profesores_nocturno_job",
                    replace_existing=True
                )
                scheduler.add_job(
                    run_notificar_clases_una_alumna_job,
                    trigger="cron",
                    hour=9,
                    minute=15,
                    id="asistente_notificar_clases_una_alumna_job",
                    replace_existing=True
                )
                scheduler.add_job(
                    run_solicitar_asistencia_profesores_job,
                    trigger="interval",
                    minutes=15,
                    id="asistente_solicitar_asistencia_profesores_job",
                    replace_existing=True
                )
                scheduler.add_job(
                    run_alertar_vencimiento_abonos_job,
                    trigger="cron",
                    hour=10,
                    minute=30,
                    id="asistente_alertar_vencimiento_abonos_job",
                    replace_existing=True
                )
                scheduler.add_job(
                    run_feedback_primera_clase_job,
                    trigger="cron",
                    hour=20,
                    minute=30,
                    id="asistente_feedback_primera_clase_job",
                    replace_existing=True
                )
                scheduler.add_job(
                    run_resumen_diario_duena_job,
                    trigger="cron",
                    hour=21,
                    minute=5,
                    id="asistente_resumen_diario_duena_job",
                    replace_existing=True
                )
                scheduler.start()
                logger.info("[ASISTENTE IA] Scheduler proactivo iniciado: ocupación (30m), recordatorios (15m), cancelación bajo cupo (60m), agenda profes (21hs), vencimientos (10:30hs), feedback (20:30hs), resumen dueña (21:05hs).")
            except Exception as e:
                logger.warning(f"[ASISTENTE IA] Scheduler proactivo no iniciado: {e}")
