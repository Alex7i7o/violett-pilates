import re

with open('core/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_model = """
class TransaccionBancaria(models.Model):
    ESTADO_CHOICES = (
        ('DISPONIBLE', 'Disponible'),
        ('CONCILIADA', 'Conciliada'),
        ('IGNORADA', 'Ignorada'),
    )
    
    mp_payment_id = models.CharField(max_length=100, unique=True, db_index=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_acreditacion = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='DISPONIBLE')
    datos_raw = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"TX {self.mp_payment_id} - ${self.monto} ({self.estado})"
"""

content += new_model

with open('core/models.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Model added")
