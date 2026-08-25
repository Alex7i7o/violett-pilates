import re

# 1. core/profesor_views.py
with open('core/profesor_views.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    "turnos_hoy = Turno.objects.filter(",
    "turnos_hoy = Turno.objects.select_related('clase', 'profesor').prefetch_related('reservas').filter("
)
c = c.replace(
    "turnos_semana = Turno.objects.filter(",
    "turnos_semana = Turno.objects.select_related('clase', 'profesor').prefetch_related('reservas').filter("
)
c = c.replace(
    "turnos_libres = Turno.objects.filter(",
    "turnos_libres = Turno.objects.select_related('clase', 'profesor').prefetch_related('reservas').filter("
)
c = c.replace(
    "plantillas_libres = PlantillaTurno.objects.filter(",
    "plantillas_libres = PlantillaTurno.objects.select_related('clase', 'profesor').filter("
)
c = c.replace(
    "mis_plantillas = PlantillaTurno.objects.filter(",
    "mis_plantillas = PlantillaTurno.objects.select_related('clase', 'profesor').filter("
)

with open('core/profesor_views.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 2. core/admin_views.py
with open('core/admin_views.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    "turnos = Turno.objects.filter(",
    "turnos = Turno.objects.select_related('clase', 'profesor').prefetch_related('reservas__usuario').filter("
)
c = c.replace(
    "reservas = Reserva.objects.filter(",
    "reservas = Reserva.objects.select_related('usuario', 'turno').filter("
)
c = c.replace(
    "queryset = PlantillaTurno.objects.filter(",
    "queryset = PlantillaTurno.objects.select_related('clase', 'profesor').filter("
)

with open('core/admin_views.py', 'w', encoding='utf-8') as f:
    f.write(c)


# 3. core/views.py
with open('core/views.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    "turnos = Turno.objects.filter(",
    "turnos = Turno.objects.select_related('clase', 'profesor').prefetch_related('reservas').filter("
)
c = c.replace(
    "recurrencias = Recurrencia.objects.filter(",
    "recurrencias = Recurrencia.objects.select_related('clase', 'usuario').filter("
)

with open('core/views.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Queries optimized")
