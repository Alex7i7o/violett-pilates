# Developed by FireSeed - Fueling Innovation
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import MinValueValidator

class ConfiguracionGlobal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cupo_maximo_defecto = models.IntegerField(default=3, validators=[MinValueValidator(1)])
    cupo_minimo_defecto = models.IntegerField(default=2, validators=[MinValueValidator(1)])
    horas_limite_cancelacion = models.IntegerField(default=24)
    horas_evaluacion_automatica = models.IntegerField(default=25)
    dias_vencimiento_plan = models.IntegerField(default=30)
    dias_alerta_vencimiento = models.IntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'configuracion_global'
        verbose_name = 'Configuración Global'
        verbose_name_plural = 'Configuración Global'

    def save(self, *args, **kwargs):
        if not self.pk and ConfiguracionGlobal.objects.exists():
            return # Only one configuration allowed
        return super(ConfiguracionGlobal, self).save(*args, **kwargs)


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
        extra_fields.setdefault('rol', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, nombre, apellido, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = (
        ('CLIENTE', 'Cliente'),
        ('ADMIN', 'Administrador'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
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


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    cantidad_clases = models.IntegerField(validators=[MinValueValidator(1)])
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'planes'

    def __str__(self):
        return self.nombre


class Suscripcion(models.Model):
    ESTADO_CHOICES = (
        ('ACTIVO', 'Activo'),
        ('AGOTADO', 'Agotado'),
        ('VENCIDO', 'Vencido'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='suscripciones')
    plan = models.ForeignKey(Plan, on_delete=models.RESTRICT, related_name='suscripciones')
    clases_restantes = models.IntegerField(validators=[MinValueValidator(0)])
    fecha_inicio = models.DateField()
    fecha_vencimiento = models.DateField(db_index=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO', db_index=True)

    class Meta:
        db_table = 'suscripciones'


class Clase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    duracion_minutos = models.IntegerField(default=60)
    cupo_maximo = models.IntegerField(validators=[MinValueValidator(1)])
    cupo_minimo = models.IntegerField(validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'clases'

    def __str__(self):
        return self.nombre


class Turno(models.Model):
    ESTADO_CHOICES = (
        ('PROGRAMADO', 'Programado'),
        ('CONFIRMADO', 'Confirmado'),
        ('CANCELADO', 'Cancelado'),
        ('COMPLETADO', 'Completado'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='turnos')
    fecha = models.DateField(db_index=True)
    hora_inicio = models.TimeField(db_index=True)
    hora_fin = models.TimeField()
    cupo_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PROGRAMADO', db_index=True)
    evaluado_25hs = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'turnos'
        constraints = [
            models.UniqueConstraint(fields=['fecha', 'hora_inicio', 'clase'], name='unique_turno'),
            models.CheckConstraint(check=models.Q(cupo_actual__gte=0), name='check_cupo_minimo')
        ]
        indexes = [
            models.Index(fields=['fecha', 'hora_inicio'], name='idx_turnos_fecha_hora'),
        ]


class Recurrencia(models.Model):
    DIA_SEMANA_CHOICES = (
        (1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'),
        (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado'), (7, 'Domingo'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='recurrencias')
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='recurrencias')
    dia_semana = models.IntegerField(choices=DIA_SEMANA_CHOICES)
    hora_inicio = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'recurrencias'
        constraints = [
            models.UniqueConstraint(fields=['clase', 'dia_semana', 'hora_inicio', 'usuario'], name='unique_recurrencia')
        ]


class Reserva(models.Model):
    ESTADO_CHOICES = (
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA_TIEMPO', 'Cancelada a Tiempo'),
        ('CANCELADA_TARDIA', 'Cancelada Tardía'),
        ('TOMADA', 'Tomada'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name='reservas')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas')
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.RESTRICT, related_name='reservas')
    es_recurrente = models.BooleanField(default=False)
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='CONFIRMADA', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservas'
        constraints = [
            models.UniqueConstraint(fields=['turno', 'usuario'], name='unique_reserva_usuario')
        ]
        indexes = [
            models.Index(fields=['usuario', 'estado'], name='idx_reservas_usuario_estado'),
        ]
