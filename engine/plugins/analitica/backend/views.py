from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from core.models import Usuario, Turno, Reserva
from .models import MetricaInteractiva, RegistroFacturacion
import datetime

class AnaliticaDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        month = int(request.query_params.get('month', now.month))
        year = int(request.query_params.get('year', now.year))
        
        # Helper to filter by month/year
        def in_month(qs, date_field):
            return qs.filter(**{f"{date_field}__month": month, f"{date_field}__year": year})

        # 1. EL MOTOR DE VALOR (Impacto)
        metricas = in_month(MetricaInteractiva.objects, 'fecha')
        total_emails = metricas.filter(tipo='EMAIL').count()
        total_wpps = metricas.filter(tipo='WPP').count()
        auto_reservas = metricas.filter(tipo='AUTO_RESERVA').count()
        auto_cancels = metricas.filter(tipo='AUTO_CANCEL').count()
        
        # Asumiendo 5 minutos ahorrados por cada acción automatizada
        acciones_totales = total_emails + total_wpps + auto_reservas + auto_cancels
        minutos_ahorrados = acciones_totales * 5
        horas_ahorradas = round(minutos_ahorrados / 60, 1)

        # 2. RADIOGRAFÍA DE LA COMUNIDAD (Demografía)
        clientes = Usuario.objects.filter(rol='CLIENTE')
        total_alumnos = clientes.count()
        
        # Nuevos alumnos este mes
        nuevos_alumnos = in_month(clientes, 'created_at').count()
        
        # Calcular edad y sexo iterando (ya que FichaMedica no es required de forma nativa en db para aggregation)
        generos = {'F': 0, 'M': 0, 'O': 0, 'N': 0}
        edades = {'<20': 0, '20-30': 0, '31-40': 0, '41-50': 0, '>50': 0}
        suma_edades = 0
        count_edades = 0

        for cliente in clientes.select_related('ficha_medica'):
            if hasattr(cliente, 'ficha_medica'):
                ficha = cliente.ficha_medica
                if ficha.sexo in generos:
                    generos[ficha.sexo] += 1
                if ficha.fecha_nacimiento:
                    edad = now.date().year - ficha.fecha_nacimiento.year - ((now.date().month, now.date().day) < (ficha.fecha_nacimiento.month, ficha.fecha_nacimiento.day))
                    suma_edades += edad
                    count_edades += 1
                    if edad < 20: edades['<20'] += 1
                    elif 20 <= edad <= 30: edades['20-30'] += 1
                    elif 31 <= edad <= 40: edades['31-40'] += 1
                    elif 41 <= edad <= 50: edades['41-50'] += 1
                    else: edades['>50'] += 1

        promedio_edad = round(suma_edades / count_edades) if count_edades > 0 else 0

        # 3. FACTURACIÓN
        facturacion_qs = in_month(RegistroFacturacion.objects, 'fecha')
        total_facturacion = facturacion_qs.aggregate(Sum('monto'))['monto__sum'] or 0

        # Desglose por plan
        desglose_planes = list(facturacion_qs.values('plan_nombre').annotate(total=Sum('monto'), cantidad=Count('id')).order_by('-total'))

        # 4. SALUD OPERATIVA
        turnos_mes = in_month(Turno.objects, 'fecha')
        turnos_realizados = turnos_mes.filter(estado__in=['PROGRAMADO', 'COMPLETADO', 'REALIZADO'])
        turnos_cancelados = turnos_mes.filter(estado='CANCELADO').count()
        
        ocupacion = 0
        heatmap = {}
        for t in turnos_realizados:
            capacidad = t.clase.cupo_maximo
            ocupados = capacidad - t.cupo_actual
            if capacidad > 0:
                ocupacion += (ocupados / capacidad)
                
            dia = t.fecha.isoweekday() # 1=Lunes, 7=Domingo
            hora = t.hora_inicio.strftime('%H:%M')
            key = f"{dia}-{hora}"
            if key not in heatmap:
                heatmap[key] = {'dia': dia, 'hora': hora, 'clases': 0, 'ocupacion': 0}
            heatmap[key]['clases'] += 1
            heatmap[key]['ocupacion'] += (ocupados / capacidad) if capacidad > 0 else 0
            
        promedio_ocupacion = round((ocupacion / turnos_realizados.count()) * 100) if turnos_realizados.count() > 0 else 0
        
        # Formatear heatmap
        heatmap_data = []
        for v in heatmap.values():
            heatmap_data.append({
                'dia': v['dia'],
                'hora': v['hora'],
                'ocupacion_promedio': round((v['ocupacion'] / v['clases']) * 100)
            })

        return Response({
            'valor': {
                'horas_ahorradas': horas_ahorradas,
                'auto_reservas': auto_reservas,
                'auto_cancels': auto_cancels,
                'emails_enviados': total_emails,
                'wpps_enviados': total_wpps,
                'tasa_autogestion': round((auto_reservas + auto_cancels) / max(1, acciones_totales) * 100)
            },
            'comunidad': {
                'total_alumnos': total_alumnos,
                'nuevos_alumnos': nuevos_alumnos,
                'promedio_edad': promedio_edad,
                'distribucion_genero': generos,
                'distribucion_edad': edades
            },
            'facturacion': {
                'total': total_facturacion,
                'desglose_planes': desglose_planes
            },
            'operatividad': {
                'promedio_ocupacion': promedio_ocupacion,
                'clases_dictadas': turnos_realizados.count(),
                'clases_canceladas': turnos_cancelados,
                'heatmap': heatmap_data
            }
        })
