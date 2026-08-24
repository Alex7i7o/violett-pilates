from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum
from .models import Turno, Profesor, PlantillaTurno
from .serializers import AdminTurnoSerializer, PlantillaTurnoSerializer
import datetime

class IsProfesorPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.rol == 'PROFESOR'

class ProfesorDashboardView(views.APIView):
    permission_classes = [IsProfesorPermission]

    def get(self, request):
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
        start_of_month = today.replace(day=1)

        # Horas totales este mes (contabilizadas por turnos COMPLETADOS o PROGRAMADOS ya confirmados para él)
        # Asumiendo cada turno dura 'duracion_minutos' que por defecto era 60 o podemos simplemente contar turnos.
        # Contaremos turnos y asumiremos 1 hora por turno para simplificar, o extraeremos horas de la BD.
        # Wait, Turno model has no duracion_minutos, but Clase does?
        # Let's just count turnos * 1 hour for now, or use Turno.hora_inicio/fin diff.
        turnos_mes = Turno.objects.filter(
            profesor=profesor,
            fecha__gte=start_of_month,
            fecha__lte=today,
            estado__in=['PROGRAMADO', 'COMPLETADO']
        )
        
        horas_dictadas = len(turnos_mes) # Simplified 1h per class

        # Hoy
        turnos_hoy = Turno.objects.filter(
            profesor=profesor,
            fecha=today,
            estado='PROGRAMADO'
        ).order_by('hora_inicio')

        # Esta semana (excluyendo hoy para no duplicar en UI)
        turnos_semana = Turno.objects.filter(
            profesor=profesor,
            fecha__gt=today,
            fecha__lte=end_of_week,
            estado='PROGRAMADO'
        ).order_by('fecha', 'hora_inicio')

        # Clases sin asignar (futuras a partir de hoy)
        turnos_libres = Turno.objects.filter(
            profesor__isnull=True,
            fecha__gte=today,
            estado='PROGRAMADO'
        ).order_by('fecha', 'hora_inicio')
        
        # Horarios fijos sin profesor asignado
        plantillas_libres = PlantillaTurno.objects.filter(
            profesor__isnull=True,
            is_active=True
        ).order_by('dia_semana', 'hora_inicio')

        return Response({
            "horas_mes": horas_dictadas,
            "turnos_hoy": AdminTurnoSerializer(turnos_hoy, many=True).data,
            "turnos_semana": AdminTurnoSerializer(turnos_semana, many=True).data,
            "turnos_libres": AdminTurnoSerializer(turnos_libres, many=True).data,
            "plantillas_libres": PlantillaTurnoSerializer(plantillas_libres, many=True).data,
        })


class AssignClaseView(views.APIView):
    permission_classes = [IsProfesorPermission]

    def post(self, request, turno_id):
        user = request.user
        try:
            profesor = user.profesor_profile
        except Profesor.DoesNotExist:
            return Response({"detail": "Perfil de profesor no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            turno = Turno.objects.get(id=turno_id, estado='PROGRAMADO')
        except Turno.DoesNotExist:
            return Response({"detail": "Turno no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if turno.profesor is not None:
            return Response({"detail": "Este turno ya tiene profesor asignado."}, status=status.HTTP_400_BAD_REQUEST)

        turno.profesor = profesor
        turno.save()

        return Response({"detail": "Turno asignado exitosamente."})

class AssignPlantillaView(views.APIView):
    permission_classes = [IsProfesorPermission]

    def post(self, request, plantilla_id):
        user = request.user
        try:
            profesor = user.profesor_profile
        except Profesor.DoesNotExist:
            return Response({'detail': 'Perfil no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            plantilla = PlantillaTurno.objects.get(id=plantilla_id, is_active=True)
        except PlantillaTurno.DoesNotExist:
            return Response({'detail': 'Plantilla no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if plantilla.profesor is not None:
            return Response({'detail': 'Este horario fijo ya tiene profesor.'}, status=status.HTTP_400_BAD_REQUEST)

        plantilla.profesor = profesor
        plantilla.save()

        # Auto-asignar turnos futuros generados por esta plantilla que an no tengan profesor
        Turno.objects.filter(plantilla=plantilla, fecha__gte=timezone.now().date(), profesor__isnull=True).update(profesor=profesor)

        return Response({'detail': 'Plantilla asignada exitosamente.'})
