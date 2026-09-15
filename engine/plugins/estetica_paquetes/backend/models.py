import uuid
from django.db import models
from django.utils import timezone
from plugins.estetica_servicios.backend.models import ServicioEstetica
from core.models import Usuario

class ReglaPaquete(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cantidad_sesiones = models.IntegerField(default=1)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'estetica_regla_paquete'

class BilleteraCliente(models.Model):
    ESTADOS = (
        ('ACTIVO', 'Activo'),
        ('AGOTADO', 'Agotado'),
        ('VENCIDO', 'Vencido'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='paquetes_comprados')
    servicio = models.ForeignKey(ServicioEstetica, on_delete=models.CASCADE, related_name='billeteras')
    sesiones_totales = models.IntegerField()
    sesiones_restantes = models.IntegerField()
    fecha_compra = models.DateField(default=timezone.now)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVO')

    class Meta:
        db_table = 'estetica_billetera_cliente'
