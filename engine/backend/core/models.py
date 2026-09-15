import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator
from django.utils import timezone

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, apellido, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, apellido=apellido, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, apellido, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nombre, apellido, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = (
        ('CLIENTE', 'Cliente'),
        ('PROFESOR', 'Profesor'),
        ('ADMIN', 'Administrador'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, default='')
    apellido = models.CharField(max_length=100, default='')
    email = models.EmailField(unique=True, max_length=255)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    google_id = models.CharField(max_length=255, unique=True, blank=True, null=True, db_index=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='CLIENTE')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Clase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, default='')
    descripcion = models.TextField(blank=True, null=True)
    duracion_minutos = models.IntegerField(default=60)
    cupo_maximo = models.IntegerField(default=10)
    cupo_minimo = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'clases'
        
    def __str__(self):
        return self.nombre



class PlantillaTurno(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='plantillas')
    dia_semana = models.IntegerField() # 1=Lunes..7=Domingo
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'plantillas_turno'

class Turno(models.Model):
    ESTADO_CHOICES = (
        ('PROGRAMADO', 'Programado'),
        ('CANCELADO', 'Cancelado'),
        ('COMPLETADO', 'Completado'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plantilla = models.ForeignKey(PlantillaTurno, on_delete=models.SET_NULL, null=True, blank=True, related_name='turnos_generados')
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='turnos')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    cupo_actual = models.IntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PROGRAMADO')
    evaluado_25hs = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if self._state.adding and self.cupo_actual == 0:
            if self.clase_id:
                clase_obj = Clase.objects.get(pk=self.clase_id)
                self.cupo_actual = clase_obj.cupo_maximo
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'turnos'
        indexes = [
            models.Index(fields=['fecha', 'estado']),
        ]

class Reserva(models.Model):
    ESTADO_CHOICES = (
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA_TIEMPO', 'Cancelada a Tiempo'),
        ('CANCELADA_TARDIA', 'Cancelada Tardía'),
        ('TOMADA', 'Tomada'),
        ('AUSENTE', 'Ausente'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name='reservas')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas')
    created_at = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='CONFIRMADA', db_index=True)
    es_recurrente = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'reservas'
        unique_together = ('turno', 'usuario')

