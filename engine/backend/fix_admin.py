import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))

# Force SQLite
os.environ['DATABASE_URL'] = "sqlite:///db.sqlite3"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_core.settings")

import django
django.setup()

from core.models import Usuario
from plugins.profesores.backend.models import Profesor

email = 'alexxaguero@gmail.com'
try:
    p = Profesor.objects.get(email=email)
    print("Found profesor:", p.nombre)
    u = Usuario.objects.filter(email=email).first()
    if not u:
        u = Usuario.objects.create_user(email=email, nombre=p.nombre, apellido=p.apellido, password='profesor123', rol='PROFESOR')
        print("Created user for profesor.")
    else:
        u.set_password('profesor123')
        u.rol = 'PROFESOR'
        u.save()
        print("User already existed, updated password and role.")
    p.usuario = u
    p.save()
    print("Linked user to profesor.")
except Exception as e:
    print("Error:", e)
