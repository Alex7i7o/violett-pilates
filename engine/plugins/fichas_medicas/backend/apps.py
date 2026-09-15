from django.apps import AppConfig


class FichasMedicasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.fichas_medicas.backend'
    label = 'fichas_medicas'

    def ready(self):
        try:
            import plugins.fichas_medicas.backend.hooks
        except ImportError:
            pass
