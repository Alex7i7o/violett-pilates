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
