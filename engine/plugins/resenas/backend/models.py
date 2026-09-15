from django.db import models
from core.models import Usuario

class Resena(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas')
    estrellas = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    mensaje = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña de {self.usuario.email} - {self.estrellas} estrellas"
