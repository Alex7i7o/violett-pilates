import uuid
from django.db import models
from django.utils import timezone
from plugins.estetica_servicios.backend.models import ServicioEstetica
from core.models import Usuario

class DisponibilidadDia(models.Model):
    DIAS = (
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dia_semana = models.IntegerField(choices=DIAS, unique=True)
    is_active = models.BooleanField(default=True)
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()
    break_inicio = models.TimeField(blank=True, null=True)
    break_fin = models.TimeField(blank=True, null=True)

    class Meta:
        db_table = 'estetica_disponibilidad_dia'

class ReservaEstetica(models.Model):
    ESTADOS = (
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('ASISTIO', 'Asistió'),
        ('NO_ASISTIO', 'No Asistió'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas_estetica')
    servicio = models.ForeignKey(ServicioEstetica, on_delete=models.CASCADE, related_name='reservas_agendadas')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='CONFIRMADA')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'estetica_reserva'
