from django.apps import AppConfig

class MembresiasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.membresias.backend'
    label = 'membresias'

    def ready(self):
        import plugins.membresias.backend.hooks
