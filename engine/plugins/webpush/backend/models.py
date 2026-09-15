from django.db import models
from django.conf import settings

class PushSubscription(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Subscription for {self.usuario.email}"