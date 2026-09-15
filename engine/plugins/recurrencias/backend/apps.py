from django.apps import AppConfig


class RecurrenciasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.recurrencias.backend'
    label = 'recurrencias'

    def ready(self):
        try:
            import plugins.recurrencias.backend.hooks
        except ImportError:
            pass
