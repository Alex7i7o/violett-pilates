from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
import datetime

from .models import Profesor, PlantillaProfesor, TurnoProfesor

from .serializers import ProfesorSerializer
from core.models import Turno, PlantillaTurno

class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.filter(is_active=True)
    serializer_class = ProfesorSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        profesor = serializer.save()
        if profesor.email:
            try:
                import string
                import random
                from core.models import Usuario
                from core.services import enviar_email_bienvenida
                
                raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                u = Usuario.objects.create_user(
                    email=profesor.email,
                    nombre=profesor.nombre,
                    apellido=profesor.apellido,
                    password=raw_password,
                    rol='PROFESOR'
                )
                profesor.usuario = u
                profesor.save()
                
                enviar_email_bienvenida(u, raw_password)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error creando usuario profesor: {e}")
                pass

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class ProfesorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.rol != 'PROFESOR':
            return Response({"detail": "No tienes permiso."}, status=403)
            
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        now = timezone.now()
        
        if not month or not year:
            month = now.month
            year = now.year
        else:
            month = int(month)
            year = int(year)

        turnos = Turno.objects.filter(estado='PROGRAMADO').order_by('fecha', 'hora_inicio')
        turnos_hoy = [t for t in turnos if t.fecha == now.date()]
        turnos_semana = [t for t in turnos if t.fecha > now.date() and t.fecha <= now.date() + datetime.timedelta(days=7)]
        turnos_mes = [t for t in turnos if t.fecha.month == month and t.fecha.year == year]

        plantillas = PlantillaTurno.objects.filter(is_active=True).order_by('dia_semana', 'hora_inicio')

        def serialize_turno(t):
            return {
                "id": str(t.id),
                "fecha": t.fecha.isoformat(),
                "hora_inicio": t.hora_inicio.strftime('%H:%M'),
                "hora_fin": t.hora_fin.strftime('%H:%M'),
                "clase_nombre": t.clase.nombre,
                "estado": t.estado
            }

        def serialize_plantilla(p):
            return {
                "id": str(p.id),
                "dia_semana": p.dia_semana,
                "hora_inicio": p.hora_inicio.strftime('%H:%M'),
                "hora_fin": p.hora_fin.strftime('%H:%M'),
                "clase_nombre": p.clase.nombre
            }

        # Real Bolsa logic
        profesor_id = None
        if hasattr(request.user, 'profesor_plugin_profile'):
            profesor_id = request.user.profesor_plugin_profile.id
            
        unassigned_turnos = Turno.objects.filter(profesor_asignado__isnull=True, fecha__gte=now.date())
        unassigned_plantillas = PlantillaTurno.objects.filter(profesor_asignado__isnull=True)
        
        turnos_libres = [serialize_turno(t) for t in unassigned_turnos]
        plantillas_libres = [serialize_plantilla(p) for p in unassigned_plantillas]
        
        return Response({
            "mis_plantillas": [serialize_plantilla(p) for p in plantillas],
            "horas_mes": len(turnos_mes),
            "turnos_mes_historial": [serialize_turno(t) for t in turnos_mes],
            "turnos_hoy": [serialize_turno(t) for t in turnos_hoy],
            "turnos_semana": [serialize_turno(t) for t in turnos_semana],
            "turnos_libres": turnos_libres,
            "plantillas_libres": plantillas_libres
        })
from rest_framework import status
from django.db import transaction

class AssignPlantillaView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            profesor = request.user.profesor_plugin_profile
            plantilla = PlantillaTurno.objects.get(id=pk)
            
            # Create or update assignment
            PlantillaProfesor.objects.update_or_create(
                plantilla=plantilla,
                defaults={'profesor': profesor}
            )
            return Response({"detail": "Plantilla asignada exitosamente"})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AssignTurnoView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            profesor = request.user.profesor_plugin_profile
            turno = Turno.objects.get(id=pk)
            
            TurnoProfesor.objects.update_or_create(
                turno=turno,
                defaults={'profesor': profesor}
            )
            return Response({"detail": "Turno asignado exitosamente"})
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
