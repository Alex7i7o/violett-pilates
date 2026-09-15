import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_core.settings")
django.setup()

from core.models import Usuario

# Create Admin
admin_email = "admin@violett.com"
if not Usuario.objects.filter(email=admin_email).exists():
    admin = Usuario.objects.create_superuser(
        email=admin_email,
        password="password123",
        nombre="Administrador",
        apellido="Violett"
    )
    admin.rol = 'ADMIN'
    admin.save()
    print("Admin creado: admin@violett.com / password123")
else:
    admin = Usuario.objects.get(email=admin_email)
    admin.set_password("password123")
    admin.save()
    print("Admin actualizado: admin@violett.com / password123")

# Create Client
alumno_email = "alumno@violett.com"
if not Usuario.objects.filter(email=alumno_email).exists():
    alumno = Usuario.objects.create_user(
        email=alumno_email,
        password="password123",
        nombre="Alumna",
        apellido="Prueba"
    )
    alumno.rol = 'CLIENTE'
    alumno.save()
    print("Alumno creado: alumno@violett.com / password123")
else:
    alumno = Usuario.objects.get(email=alumno_email)
    alumno.set_password("password123")
    alumno.save()
    print("Alumno actualizado: alumno@violett.com / password123")
