from django.apps import AppConfig

class WebpushConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plugins.webpush.backend'
    label = 'webpush'

    def ready(self):
        import plugins.webpush.backend.hooks