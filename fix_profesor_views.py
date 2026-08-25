import re

with open('core/profesor_views.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Let's replace the top part of get() in ProfesorDashboardView
old_start = '''    def get(self, request):
        user = request.user
        try:
            profesor = user.profesor_profile
        except Profesor.DoesNotExist:
            return Response({"detail": "Perfil de profesor no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        today = now.date()
        
        # Start and end of current week (Monday to Sunday)
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)

        # Start of current month
        start_of_month = today.replace(day=1)'''

new_start = '''    def get(self, request):
        user = request.user
        try:
            profesor = user.profesor_profile
        except Profesor.DoesNotExist:
            return Response({"detail": "Perfil de profesor no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        today = now.date()
        
        # Parse optional month and year
        req_month = request.query_params.get('month')
        req_year = request.query_params.get('year')
        
        if req_month and req_year:
            target_month = int(req_month)
            target_year = int(req_year)
            # Find start and end of target month
            start_of_target_month = datetime.date(target_year, target_month, 1)
            # Next month calculation
            if target_month == 12:
                next_month_start = datetime.date(target_year + 1, 1, 1)
            else:
                next_month_start = datetime.date(target_year, target_month + 1, 1)
            end_of_target_month = next_month_start - datetime.timedelta(days=1)
            
            # If target month is current month, limit to today for 'horas_dictadas' to be precise, or show whole month?
            # User wants "las que cuentan para el contador de clases" which usually means past/completed ones in that month.
            limit_date = min(end_of_target_month, today)
        else:
            start_of_target_month = today.replace(day=1)
            limit_date = today

        # Start and end of current week (Monday to Sunday) for current schedule
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
'''
c = c.replace(old_start, new_start)

# Replace turnos_mes
old_turnos_mes = '''        turnos_mes = Turno.objects.filter(
            profesor=profesor,
            fecha__gte=start_of_month,
            fecha__lte=today,
            estado__in=['PROGRAMADO', 'COMPLETADO']
        )'''
new_turnos_mes = '''        turnos_mes = Turno.objects.select_related('clase', 'profesor').filter(
            profesor=profesor,
            fecha__gte=start_of_target_month,
            fecha__lte=limit_date,
            estado__in=['PROGRAMADO', 'COMPLETADO']
        ).order_by('-fecha', '-hora_inicio')'''
c = c.replace(old_turnos_mes, new_turnos_mes)

# Replace Response
old_res = '''        return Response({
            "mis_plantillas": PlantillaTurnoSerializer(mis_plantillas, many=True).data,
            "horas_mes": horas_dictadas,
            "turnos_hoy": AdminTurnoSerializer(turnos_hoy, many=True).data,
            "turnos_semana": AdminTurnoSerializer(turnos_semana, many=True).data,
            "turnos_libres": AdminTurnoSerializer(turnos_libres, many=True).data,
            "plantillas_libres": PlantillaTurnoSerializer(plantillas_libres, many=True).data,
        })'''
new_res = '''        return Response({
            "mis_plantillas": PlantillaTurnoSerializer(mis_plantillas, many=True).data,
            "horas_mes": horas_dictadas,
            "turnos_mes_historial": AdminTurnoSerializer(turnos_mes, many=True).data,
            "turnos_hoy": AdminTurnoSerializer(turnos_hoy, many=True).data,
            "turnos_semana": AdminTurnoSerializer(turnos_semana, many=True).data,
            "turnos_libres": AdminTurnoSerializer(turnos_libres, many=True).data,
            "plantillas_libres": PlantillaTurnoSerializer(plantillas_libres, many=True).data,
        })'''
c = c.replace(old_res, new_res)

with open('core/profesor_views.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Profesor views updated")
