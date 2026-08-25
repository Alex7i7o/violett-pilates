import sys

with open('core/views.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''        if is_recurring:
            weekday = turno.fecha.isoweekday()
            active_recs = Recurrencia.objects.filter('''

replacement = '''        if is_recurring:
            if not getattr(turno, 'plantilla_id', None):
                return Response({"detail": "Esta clase es puntual y no admite reserva recurrente."}, status=status.HTTP_400_BAD_REQUEST)
            weekday = turno.fecha.isoweekday()
            active_recs = Recurrencia.objects.filter('''

c = c.replace(target, replacement)

with open('core/views.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Done")
