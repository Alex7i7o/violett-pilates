from django.apps import AppConfig
import sys

class AutomatizacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.automatizaciones.backend'
    label = 'automatizaciones'

    def ready(self):
        # Prevent running scheduler twice in dev or during migrations
        if any(cmd in arg for arg in sys.argv for cmd in ['makemigrations', 'migrate', 'collectstatic', 'shell', 'test']):
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from django_apscheduler.jobstores import DjangoJobStore, register_events
            from django.core.management import call_command
            
            scheduler = BackgroundScheduler()
            scheduler.add_jobstore(DjangoJobStore(), "default")
            
            @scheduler.scheduled_job("interval", minutes=15, id="cancel_empty_classes_job", replace_existing=True)
            def run_cancel_empty_classes():
                call_command("cancel_empty_classes")
                
            register_events(scheduler)
            scheduler.start()
            
            # Ejecutar Inmediatamente al iniciar
            import threading
            threading.Timer(5.0, run_cancel_empty_classes).start()
            print("Automatizaciones Scheduler started.")
        except Exception as e:
            print("Scheduler failed to start:", e)
