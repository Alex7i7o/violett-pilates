import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class ConversacionWhatsApp(models.Model):
    ROLES = [
        ('ALUMNA', 'Alumna / Alumno'),
        ('PROFESOR', 'Profesor / Profesora'),
        ('DUENA', 'Dueña / Directora'),
        ('PROSPECTO', 'Contacto no registrado'),
    ]

    ESTADOS = [
        ('ACTIVO', 'Activa (Atendida por IA)'),
        ('ESPERANDO_HUMANO', 'Pausada (Esperando atención humana)'),
        ('CERRADO', 'Cerrada / Resuelta'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    telefono = models.CharField(max_length=30, unique=True, db_index=True, help_text="Número internacional E.164")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversaciones_ia')
    rol_detectado = models.CharField(max_length=20, choices=ROLES, default='PROSPECTO')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVO')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conversación de Asistente'
        verbose_name_plural = 'Conversaciones de Asistente'
        ordering = ['-updated_at']

    def __str__(self):
        user_name = f" ({self.usuario.nombre})" if self.usuario and hasattr(self.usuario, 'nombre') else ""
        return f"{self.telefono}{user_name} - {self.rol_detectado} [{self.estado}]"


class MensajeWhatsAppLog(models.Model):
    DIRECCIONES = [
        ('ENTRANTE', 'Entrante (Del usuario)'),
        ('SALIENTE', 'Saliente (De la IA)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversacion = models.ForeignKey(ConversacionWhatsApp, on_delete=models.CASCADE, related_name='mensajes')
    direccion = models.CharField(max_length=10, choices=DIRECCIONES)
    agente_responsable = models.CharField(max_length=50, default='supervisor')
    texto = models.TextField()
    tokens_utilizados = models.PositiveIntegerField(default=0)
    tools_ejecutadas = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Mensaje WhatsApp'
        verbose_name_plural = 'Logs de Mensajes WhatsApp'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.direccion}] {self.conversacion.telefono}: {self.texto[:40]}..."


class RegistroAccionIA(models.Model):
    TIPOS = [
        ('RESERVA_CREADA', 'Reserva de Camilla Creada'),
        ('RESERVA_CANCELADA', 'Reserva Cancelada'),
        ('TURNO_REASIGNADO', 'Reemplazo de Profesor Asignado'),
        ('PLAN_REACTIVADO', 'Plan Reactivado / Acreditado'),
        ('ALUMNO_REGISTRADO', 'Alta de Alumno Guiada'),
        ('REPORTE_DUENA', 'Reporte Solicitado por Dueña'),
        ('OFERTA_PROACTIVA', 'Oferta Proactiva de Camilla Libre'),
        ('PROPUESTA_CONSOLIDACION', 'Sugerencia de Fusión de Clases Incompletas'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversacion = models.ForeignKey(ConversacionWhatsApp, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_accion = models.CharField(max_length=40, choices=TIPOS)
    descripcion = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Acción de Asistente IA'
        verbose_name_plural = 'Acciones de Asistente IA'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tipo_accion} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ComprobantePendiente(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Aprobación'),
        ('APROBADO', 'Aprobado y Acreditado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversacion = models.ForeignKey(ConversacionWhatsApp, on_delete=models.CASCADE, related_name='comprobantes')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='comprobantes_subidos')
    monto = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    plan_nombre = models.CharField(max_length=100, blank=True)
    plan_id = models.CharField(max_length=50, blank=True)
    datos_extraidos = models.JSONField(default=dict, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    aprobado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='comprobantes_aprobados')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Comprobante de Pago'
        verbose_name_plural = 'Comprobantes de Pago'
        ordering = ['-created_at']

    def __str__(self):
        tel = self.conversacion.telefono
        user = f" ({self.usuario.nombre})" if self.usuario else ""
        return f"Comprobante ${self.monto} - {tel}{user} [{self.estado}]"


class VinculoAlumnos(models.Model):
    TIPOS = [
        ('INSEPARABLES', 'Inseparables (Madre/Hija, Amigas, Pareja)'),
        ('FAMILIAR', 'Familiar'),
        ('AMIGAS', 'Amigas habituales'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alumna_1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vinculos_primarios')
    alumna_2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vinculos_secundarios')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='INSEPARABLES')
    observaciones = models.CharField(max_length=255, default='Vienen juntas siempre, no separar en horarios distintos.')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vínculo de Alumnos'
        verbose_name_plural = 'Vínculos de Alumnos'
        unique_together = ('alumna_1', 'alumna_2')

    def __str__(self):
        return f"{self.alumna_1.nombre} + {self.alumna_2.nombre} ({self.tipo})"


class PreferenciaAlumno(models.Model):
    FRANJAS = [
        ('MANANA', 'Mañana (8 a 13 hs)'),
        ('TARDE', 'Tarde (14 a 18 hs)'),
        ('NOCHE', 'Noche (18 a 21 hs)'),
        ('INDIFERENTE', 'Indiferente / Flexible'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferencias_ia')
    franja_preferida = models.CharField(max_length=20, choices=FRANJAS, default='INDIFERENTE')
    dias_preferidos = models.JSONField(default=list, blank=True, help_text="Lista de dias ISO (1=Lunes, 7=Domingo)")
    notas_asistente = models.TextField(blank=True, help_text="Preferencias de trato o detalles fisicos recordados por la IA")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Preferencia de Alumno'
        verbose_name_plural = 'Preferencias de Alumnos'

    def __str__(self):
        return f"Preferencias de {self.usuario.nombre} - {self.franja_preferida}"
