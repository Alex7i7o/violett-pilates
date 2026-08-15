import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fireseed_project.settings')
django.setup()

from core.models import Turno, Reserva, Suscripcion
from django.utils import timezone
import datetime

turno = Turno.objects.filter(fecha=datetime.date(2026, 8, 12)).first()
if turno:
    print("Turno found:", turno.id, turno.clase, turno.fecha, turno.hora_inicio)
    future_turnos = Turno.objects.filter(
        clase=turno.clase,
        hora_inicio=turno.hora_inicio,
        fecha__gte=turno.fecha,
        fecha__lte=datetime.date(2026, 9, 10),
        estado='PROGRAMADO',
        cupo_actual__gt=0
    ).order_by('fecha')
    print("Future turnos query count:", future_turnos.count())
    weekday = turno.fecha.isoweekday()
    future_turnos_list = [t for t in future_turnos if t.fecha.isoweekday() == weekday]
    print("Future turnos filtered:", len(future_turnos_list))
    for t in future_turnos_list:
        print(f" - {t.fecha} {t.hora_inicio} cupo: {t.cupo_actual}")
else:
    print("Turno not found.")
