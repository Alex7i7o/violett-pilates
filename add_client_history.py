import re

with open('core/views.py', 'r', encoding='utf-8') as f:
    c = f.read()

history_view = '''
class ClientHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        today = now.date()
        
        req_month = request.query_params.get('month')
        req_year = request.query_params.get('year')
        
        if req_month and req_year:
            target_month = int(req_month)
            target_year = int(req_year)
            start_date = datetime.date(target_year, target_month, 1)
            if target_month == 12:
                end_date = datetime.date(target_year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                end_date = datetime.date(target_year, target_month + 1, 1) - datetime.timedelta(days=1)
            limit_date = min(end_date, today)
        else:
            start_date = today.replace(day=1)
            limit_date = today

        # Clases que el usuario ya tuvo este mes (o hasta la fecha límite)
        # Filtramos por reservas pasadas o de hoy pero con horario finalizado
        current_time = now.time()
        
        reservas = Reserva.objects.select_related('turno', 'turno__clase', 'turno__profesor').filter(
            usuario=user,
            turno__fecha__gte=start_date,
            turno__fecha__lte=limit_date,
            estado__in=['CONFIRMADA', 'TOMADA', 'AUSENTE', 'CANCELADA_TARDIA']
        ).order_by('-turno__fecha', '-turno__hora_inicio')

        # Filter out future classes of today
        historial = []
        for r in reservas:
            if r.turno.fecha < today or (r.turno.fecha == today and r.turno.hora_fin < current_time):
                historial.append({
                    "id": r.id,
                    "turno_id": r.turno.id,
                    "fecha": r.turno.fecha.strftime("%Y-%m-%d"),
                    "hora_inicio": r.turno.hora_inicio.strftime("%H:%M"),
                    "hora_fin": r.turno.hora_fin.strftime("%H:%M"),
                    "clase_nombre": r.turno.clase.nombre,
                    "estado_reserva": r.estado
                })

        return Response(historial)
'''

# Check if already added
if 'ClientHistoryView' not in c:
    c += history_view
    with open('core/views.py', 'w', encoding='utf-8') as f:
        f.write(c)

    # Add to core/urls.py
    with open('core/urls.py', 'r', encoding='utf-8') as f:
        urls = f.read()
    
    if 'ClientHistoryView' not in urls:
        urls = urls.replace('from .views import', 'from .views import ClientHistoryView,')
        urls = urls.replace("path('profile/', ClientProfileView.as_view(), name='profile'),",
                            "path('profile/', ClientProfileView.as_view(), name='profile'),\n    path('reservas/historial/', ClientHistoryView.as_view(), name='reservas-historial'),")
        with open('core/urls.py', 'w', encoding='utf-8') as f:
            f.write(urls)
        print("ClientHistoryView added to urls.py")

print("ClientHistoryView prepared")
