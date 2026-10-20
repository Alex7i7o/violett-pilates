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
