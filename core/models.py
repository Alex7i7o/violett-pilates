import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator
from django.utils import timezone

class ConfiguracionGlobal(models.Model):
    id = models.IntegerField(primary_key=True, default=1)
    cupo_maximo_defecto = models.IntegerField(default=10)
    cupo_minimo_defecto = models.IntegerField(default=1)
    horas_limite_cancelacion = models.IntegerField(default=12)
    horas_evaluacion_automatica = models.IntegerField(default=25)
    dias_vencimiento_plan = models.IntegerField(default=30)
    dias_alerta_vencimiento = models.IntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'configuracion_global'
        verbose_name = 'Configuración Global'
        verbose_name_plural = 'Configuración Global'

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
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True, max_length=255)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    google_id = models.CharField(max_length=255, unique=True, blank=True, null=True, db_index=True)
    contacto_emergencia = models.CharField(max_length=255, blank=True, null=True)
    notas_medicas = models.TextField(blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    SEXO_CHOICES = (('F', 'Femenino'), ('M', 'Masculino'), ('O', 'Otro'), ('N', 'Prefiero no decirlo'))
    sexo = models.CharField(max_length=2, choices=SEXO_CHOICES, blank=True, null=True)
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

class Profesor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='profesor_profile')
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    sexo = models.CharField(max_length=2, choices=Usuario.SEXO_CHOICES, blank=True, null=True)
    color_identificador = models.CharField(max_length=7, default='#3B82F6')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'profesores'

class Clase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    duracion_minutos = models.IntegerField(default=60)
    cupo_maximo = models.IntegerField(default=10)
    cupo_minimo = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'clases'
        
    def __str__(self):
        return self.nombre

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
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_vencimiento = models.DateField()
    clases_restantes = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO')
    
    class Meta:
        db_table = 'suscripciones'

class PlantillaTurno(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='plantillas')
    profesor = models.ForeignKey(Profesor, on_delete=models.SET_NULL, null=True, blank=True, related_name='plantillas')
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
    profesor = models.ForeignKey(Profesor, on_delete=models.SET_NULL, null=True, blank=True, related_name='turnos')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    cupo_actual = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PROGRAMADO')
    evaluado_25hs = models.BooleanField(default=False)
    
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
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.SET_NULL, null=True, related_name='reservas_asociadas')
    created_at = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='CONFIRMADA', db_index=True)
    es_recurrente = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'reservas'
        unique_together = ('turno', 'usuario')

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

