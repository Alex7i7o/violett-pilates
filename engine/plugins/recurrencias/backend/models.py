import uuid
from django.db import models
from django.utils import timezone
from core.models import Usuario, Clase

class Recurrencia(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='recurrencias')
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
    dia_semana = models.IntegerField() # 1=Lunes, 7=Domingo (isoweekday)
    hora_inicio = models.TimeField()
    is_active = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'recurrencias'



