from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .models import Clase, PlantillaTurno, Turno, Reserva, Usuario
from .serializers import ClaseSerializer, PlantillaTurnoSerializer, AdminTurnoSerializer, AdminReservaSerializer, AdminUsuarioSerializer

class DashboardStatsView(views.APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        return Response({'usuarios': Usuario.objects.count(), 'turnos': Turno.objects.count()})

class AdminTurnoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Turno.objects.all()
    serializer_class = AdminTurnoSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        from backend_core.hooks import registry
        registry.execute("after_turno_created_manual", self.request.data, instance=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        from backend_core.hooks import registry
        registry.execute("after_turno_updated_manual", self.request.data, instance=instance)

class AdminReservaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Reserva.objects.all()
    serializer_class = AdminReservaSerializer

class ClaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Clase.objects.all()
    serializer_class = ClaseSerializer

class PlantillaTurnoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = PlantillaTurno.objects.all()
    serializer_class = PlantillaTurnoSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        from backend_core.hooks import registry
        registry.execute("after_plantilla_created", self.request.data, instance=instance)
        from .services import generar_turnos_desde_plantillas
        generar_turnos_desde_plantillas()

    def perform_update(self, serializer):
        instance = serializer.save()
        from backend_core.hooks import registry
        registry.execute("after_plantilla_updated", self.request.data, instance=instance)
        from .services import generar_turnos_desde_plantillas
        generar_turnos_desde_plantillas()


class AdminUsuarioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUsuarioSerializer

    def get_queryset(self):
        qs = Usuario.objects.filter(rol='CLIENTE')
        q = self.request.query_params.get('q', None)
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(email__icontains=q))
        return qs



from django.utils import timezone
from django.utils.dateparse import parse_date

class AdminAgendaView(views.APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        fecha_str = request.query_params.get('fecha')
        if not fecha_str:
            fecha = timezone.localdate()
        else:
            fecha = parse_date(fecha_str)

        turnos = Turno.objects.select_related('clase').prefetch_related('reservas__usuario').filter(fecha=fecha, estado__in=['PROGRAMADO', 'CONFIRMADO', 'COMPLETADO']).order_by('hora_inicio')
        serializer = AdminTurnoSerializer(turnos, many=True)
        return Response(serializer.data)
import json
import os
from django.conf import settings

class ConfiguracionView(views.APIView):
    permission_classes = [IsAdminUser]
    
    def get_config_path(self):
        # engine/config/client-config.json
        from django.conf import settings
        return os.path.join(settings.BASE_DIR, 'config', 'client-config.json')

    def get(self, request):
        try:
            with open(self.get_config_path(), 'r') as f:
                return Response(json.load(f))
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def post(self, request):
        try:
            config_path = self.get_config_path()
            with open(config_path, 'r') as f:
                cfg = json.load(f)
                
            # Allow updating specific fields safely
            # Only update plugin_config
            new_plugin_config = request.data.get('plugin_config')
            if new_plugin_config:
                cfg['plugin_config'] = new_plugin_config
                
            with open(config_path, 'w') as f:
                json.dump(cfg, f, indent=2)
                
            return Response(cfg)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

