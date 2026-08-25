import re

with open('core/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

resena_model = '''

class Resena(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas')
    puntuacion = models.IntegerField(validators=[MinValueValidator(1)])
    comentario = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resena'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Resena de {self.usuario.nombre} - {self.puntuacion} estrellas"
'''

if 'class Resena' not in content:
    with open('core/models.py', 'a', encoding='utf-8') as f:
        f.write(resena_model)
    print("Resena model added")
else:
    print("Resena model already exists")
