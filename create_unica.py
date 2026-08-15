import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fireseed_project.settings')
django.setup()
import datetime

from core.models import Clase, Turno

# Crear clase "unica pilates"
clase, created = Clase.objects.get_or_create(
    nombre="unica pilates",
    defaults={
        "descripcion": "Clase de prueba única",
        "cupo_maximo": 10,
        "cupo_minimo": 1
    }
)

# Crear turno para el jueves 13 de agosto a las 10:00 am
fecha_unica = datetime.date(2026, 8, 13)
Turno.objects.get_or_create(
    clase=clase,
    fecha=fecha_unica,
    hora_inicio="10:00",
    defaults={
        "hora_fin": "11:00",
        "cupo_actual": clase.cupo_maximo,
        "estado": "PROGRAMADO"
    }
)
print("Clase única creada exitosamente para el Jueves 13 a las 10:00 am.")
