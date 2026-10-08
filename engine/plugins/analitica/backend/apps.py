from django.apps import AppConfig

class AnaliticaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.analitica.backend'
    label = 'analitica'

    def ready(self):
        try:
            import plugins.analitica.backend.hooks
        except ImportError:
            pass
