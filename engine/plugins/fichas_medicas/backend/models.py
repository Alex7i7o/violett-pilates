import uuid
from django.db import models
from core.models import Usuario

class FichaMedica(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='ficha_medica')
    contacto_emergencia = models.CharField(max_length=255, blank=True, null=True)
    notas_medicas = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    SEXO_CHOICES = (('F', 'Femenino'), ('M', 'Masculino'), ('O', 'Otro'), ('N', 'Prefiero no decirlo'))
    sexo = models.CharField(max_length=2, choices=SEXO_CHOICES, blank=True, null=True)

    class Meta:
        db_table = 'ficha_medica'
