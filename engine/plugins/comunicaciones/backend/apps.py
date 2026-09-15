from django.apps import AppConfig

class ComunicacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.comunicaciones.backend'
    label = 'comunicaciones'

    def ready(self):
        import plugins.comunicaciones.backend.hooks
