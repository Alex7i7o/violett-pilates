import uuid
from django.db import models

class EmailLog(models.Model):
    ESTADOS = [
        ('ENVIADO', 'Enviado'),
        ('FALLIDO', 'Fallido / Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinatario = models.EmailField(max_length=255, db_index=True)
    asunto = models.CharField(max_length=255)
    template_name = models.CharField(max_length=150, blank=True, default='')
    cuerpo_html = models.TextField(blank=True, default='')
    cuerpo_texto = models.TextField(blank=True, default='')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ENVIADO', db_index=True)
    error_mensaje = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'email_logs'
        ordering = ['-created_at']
        verbose_name = 'Log de Email'
        verbose_name_plural = 'Logs de Emails'

    def __str__(self):
        return f"[{self.estado}] {self.destinatario}: {self.asunto} ({self.created_at.strftime('%d/%m/%Y %H:%M')})"
