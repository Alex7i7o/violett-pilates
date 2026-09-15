import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))
os.environ['DATABASE_URL'] = "sqlite:///db.sqlite3"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_core.settings")

import django
django.setup()

from django.test import Client
from core.models import Usuario

c = Client()
# Test as admin
admin = Usuario.objects.get(email="admin@violett.com")
c.force_login(admin)

endpoints = [
    '/api/profile/',
    '/api/turnos/disponibles/',
    '/api/admin/clases/',
    '/api/admin/plantillas/',
    '/api/admin/profesores/',
    '/api/admin/agenda/',
    '/api/admin/planes/',
    '/api/admin/alumnos/'
]

print("--- Testing Endpoints ---")
for ep in endpoints:
    resp = c.get(ep)
    print(f"GET {ep} -> {resp.status_code}")
    if resp.status_code >= 400:
        print("   ERROR:", resp.content)
