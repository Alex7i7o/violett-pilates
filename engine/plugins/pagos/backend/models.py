from django.db import models
from core.models import Usuario

class TransaccionBancaria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='transacciones_bancarias')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50, default='pendiente')
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    referencia_externa = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.usuario} - {self.monto} - {self.estado}"
