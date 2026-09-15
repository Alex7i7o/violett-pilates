import uuid
from django.db import models
from django.core.validators import MinValueValidator
from core.models import Usuario, Reserva

class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    cantidad_clases = models.IntegerField(validators=[MinValueValidator(1)])
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'plugin_planes'

    def __str__(self):
        return self.nombre

class Suscripcion(models.Model):
    ESTADO_CHOICES = (
        ('ACTIVO', 'Activo'),
        ('AGOTADO', 'Agotado'),
        ('VENCIDO', 'Vencido'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='plugin_suscripciones')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_vencimiento = models.DateField()
    clases_restantes = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO')
    
    class Meta:
        db_table = 'plugin_suscripciones'

class ReservaMembresia(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='consumo_suscripcion')
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE)

    class Meta:
        db_table = 'plugin_reservas_membresias'
