from django.apps import AppConfig

class ProfesoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.profesores.backend'
    label = 'profesores'

    def ready(self):
        from backend_core.hooks import registry
        from .hooks import enrich_turno, enrich_plantilla

        registry.register('turno_serializer', enrich_turno)
        registry.register('admin_turno_serializer', enrich_turno)
        registry.register('plantilla_serializer', enrich_plantilla)

        # Sincronización proactiva al inicio: garantiza que cualquier cambio previo en el Esquema
        # quede automáticamente reflejado en la Agenda de clases futuras.
        try:
            import threading
            from .hooks import sincronizar_profesores_esquema_con_agenda
            threading.Timer(6.0, sincronizar_profesores_esquema_con_agenda).start()
        except Exception:
            pass
