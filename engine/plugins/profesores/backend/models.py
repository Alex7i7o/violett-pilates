import uuid
from django.db import models
from core.models import Usuario, PlantillaTurno, Turno

class Profesor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='profesor_plugin_profile')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    color_identificador = models.CharField(max_length=7, default='#3B82F6')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'plugin_profesores'

class PlantillaProfesor(models.Model):
    plantilla = models.OneToOneField(PlantillaTurno, on_delete=models.CASCADE, related_name='profesor_asignado')
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)

    class Meta:
        db_table = 'plugin_plantillas_profesores'

class TurnoProfesor(models.Model):
    turno = models.OneToOneField(Turno, on_delete=models.CASCADE, related_name='profesor_asignado')
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)

    class Meta:
        db_table = 'plugin_turnos_profesores'
