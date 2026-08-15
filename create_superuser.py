import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fireseed_project.settings")
django.setup()

from core.models import Usuario

if not Usuario.objects.filter(email="admin@fireseed.com").exists():
    Usuario.objects.create_superuser("admin@fireseed.com", "Admin", "FireSeed", "admin123")
    print("Superuser created: admin@fireseed.com / admin123")
else:
    print("Superuser already exists.")
