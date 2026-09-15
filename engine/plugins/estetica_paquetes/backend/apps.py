from django.apps import AppConfig

class EsteticaPaquetesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.estetica_paquetes.backend'
    label = 'estetica_paquetes'

    def ready(self):
        import plugins.estetica_paquetes.backend.hooks
