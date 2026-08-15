import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fireseed_project.settings")
django.setup()

from core.models import Usuario, Clase, Plan, Suscripcion, Turno

# 1. Get or create user
user, created = Usuario.objects.get_or_create(
    email="alumno@violett.com",
    defaults={
        "nombre": "Ana",
        "apellido": "García",
        "rol": "CLIENTE",
    }
)
if created:
    user.set_password("violett123")
    user.save()

# 2. Create Plan
plan, _ = Plan.objects.get_or_create(
    nombre="Plan Mensual - 8 Clases",
    defaults={"cantidad_clases": 8, "precio": 35000}
)

# 3. Create Subscription
Suscripcion.objects.get_or_create(
    usuario=user,
    plan=plan,
    defaults={
        "clases_restantes": 8,
        "fecha_inicio": timezone.now().date(),
        "fecha_vencimiento": (timezone.now() + timedelta(days=30)).date(),
        "estado": "ACTIVO"
    }
)

# 4. Create Classes
clase1, _ = Clase.objects.get_or_create(nombre="Pilates Reformer", defaults={"cupo_maximo": 3, "cupo_minimo": 1})
clase2, _ = Clase.objects.get_or_create(nombre="Mat Pilates", defaults={"cupo_maximo": 5, "cupo_minimo": 2})

# 5. Create Turnos for the week
today = timezone.now().date()
for i in range(5):
    day = today + timedelta(days=i)
    # Morning slot
    Turno.objects.get_or_create(
        clase=clase1,
        fecha=day,
        hora_inicio="09:00:00",
        defaults={"hora_fin": "10:00:00", "cupo_actual": clase1.cupo_maximo}
    )
    # Evening slot
    Turno.objects.get_or_create(
        clase=clase2,
        fecha=day,
        hora_inicio="18:00:00",
        defaults={"hora_fin": "19:00:00", "cupo_actual": clase2.cupo_maximo}
    )

print("Test data created successfully! User: alumno@violett.com / violett123")
