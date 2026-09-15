import uuid
from django.db import models

class ServicioEstetica(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    duracion_minutos = models.IntegerField(default=45)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    imagen = models.ImageField(upload_to='servicios/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'estetica_servicio'
        verbose_name = 'Servicio de Estética'
        verbose_name_plural = 'Servicios de Estética'

    def __str__(self):
        return self.nombre