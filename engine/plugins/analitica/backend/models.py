import uuid
from django.db import models
from django.utils import timezone
from core.models import Usuario

class MetricaInteractiva(models.Model):
    TIPO_CHOICES = (
        ('EMAIL', 'Email Enviado'),
        ('WPP', 'WhatsApp Enviado'),
        ('AUTO_RESERVA', 'Reserva Auto-gestionada'),
        ('AUTO_CANCEL', 'Cancelación Auto-gestionada'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'plugin_analitica_metricas'

class RegistroFacturacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    plan_nombre = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    suscripcion_id = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'plugin_analitica_facturacion'
