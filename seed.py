import os, sys, django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fireseed_project.settings')
django.setup()
import datetime
from datetime import timedelta
from core.models import Clase, Turno

start_date = datetime.date.today()
end_date = start_date + timedelta(days=60)
days = [1, 2, 3, 4, 5, 6] 
times = ["09:00", "15:00", "18:00"]

turnos_creados = 0
for clase in Clase.objects.all():
    current_date = start_date
    while current_date <= end_date:
        if current_date.isoweekday() in days:
            for t in times:
                if not Turno.objects.filter(clase=clase, fecha=current_date, hora_inicio=t).exists():
                    hora_fin = (datetime.datetime.strptime(t, "%H:%M") + timedelta(hours=1)).strftime("%H:%M")
                    Turno.objects.create(
                        clase=clase,
                        fecha=current_date,
                        hora_inicio=t,
                        hora_fin=hora_fin,
                        cupo_actual=clase.cupo_maximo,
                        estado='PROGRAMADO'
                    )
                    turnos_creados += 1
        current_date += timedelta(days=1)
        
print(f"Se crearon {turnos_creados} turnos extras para todas las clases.")
