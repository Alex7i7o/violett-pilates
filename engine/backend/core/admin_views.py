from rest_framework import viewsets, views
from rest_framework.decorators import action
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
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_future = request.query_params.get('future') == 'true'
        
        if delete_future:
            from backend_core.hooks import registry
            registry.execute(
                "after_slot_destroyed", 
                {}, 
                clase_id=instance.clase_id, 
                dia_semana=instance.fecha.isoweekday(), 
                hora_inicio=instance.hora_inicio
            )
            
            from core.models import PlantillaTurno
            if instance.plantilla:
                instance.plantilla.delete()
            else:
                PlantillaTurno.objects.filter(
                    clase_id=instance.clase_id,
                    dia_semana=instance.fecha.isoweekday(),
                    hora_inicio=instance.hora_inicio
                ).delete()
            
            future_turnos = Turno.objects.filter(
                clase_id=instance.clase_id,
                fecha__gte=instance.fecha,
                hora_inicio=instance.hora_inicio
            )
            target_weekday = instance.fecha.isoweekday()
            ids_to_delete = [t.id for t in future_turnos if t.fecha.isoweekday() == target_weekday]
            if ids_to_delete:
                Turno.objects.filter(id__in=ids_to_delete).delete()
            else:
                instance.delete()
            
            return Response(status=204)
            
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save()
        alumnos = self.request.data.get('alumnos', [])
        for alumno_id in alumnos:
            usuario = Usuario.objects.filter(id=alumno_id).first()
            if usuario:
                Reserva.objects.create(turno=instance, usuario=usuario, estado='CONFIRMADA')
        
        from backend_core.hooks import registry
        registry.execute("after_turno_created_manual", self.request.data, instance=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        alumnos = self.request.data.get('alumnos', None)
        if alumnos is not None:
            current_reservas = Reserva.objects.filter(turno=instance).exclude(estado__in=['CANCELADA_TIEMPO', 'CANCELADA_TARDIA'])
            current_alumnos_ids = set(str(u_id) for u_id in current_reservas.values_list('usuario_id', flat=True))
            new_alumnos_ids = set(str(a) for a in alumnos)
            
            # To add
            for alumno_id in new_alumnos_ids - current_alumnos_ids:
                usuario = Usuario.objects.filter(id=alumno_id).first()
                if usuario:
                    Reserva.objects.create(turno=instance, usuario=usuario, estado='CONFIRMADA')
            
            # To remove
            for reserva in current_reservas:
                if str(reserva.usuario_id) not in new_alumnos_ids:
                    reserva.estado = 'CANCELADA_TIEMPO'
                    reserva.save()
                    
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

    def _deduplicate_turnos(self, instance, now):
        from collections import defaultdict
        turnos = Turno.objects.filter(
            clase=instance.clase,
            fecha__gte=now,
            hora_inicio=instance.hora_inicio
        ).prefetch_related('reservas')
        
        by_date = defaultdict(list)
        for t in turnos:
            if t.fecha.isoweekday() == instance.dia_semana:
                by_date[t.fecha].append(t)
                
        for d, t_list in by_date.items():
            if len(t_list) > 1:
                t_list.sort(key=lambda x: x.reservas.exclude(estado__in=['CANCELADA_TIEMPO', 'CANCELADA_TARDIA']).count(), reverse=True)
                primary = t_list[0]
                primary.plantilla = instance
                primary.save()
                
                for duplicate in t_list[1:]:
                    for r in duplicate.reservas.all():
                        if not primary.reservas.filter(usuario=r.usuario).exists():
                            r.turno = primary
                            r.save()
                    duplicate.delete()

    def perform_update(self, serializer):
        old_instance = PlantillaTurno.objects.get(pk=serializer.instance.pk)
        old_dia = old_instance.dia_semana
        old_hora = old_instance.hora_inicio
        old_clase_id = old_instance.clase_id
        
        instance = serializer.save()
        
        import datetime
        from django.utils import timezone
        now = timezone.localdate()
        
        # 1. Update future turnos attached to this plantilla
        future_turnos = Turno.objects.filter(plantilla=instance, fecha__gte=now)
        for t in future_turnos:
            t.clase = instance.clase
            t.hora_inicio = instance.hora_inicio
            t.hora_fin = instance.hora_fin
            
            if old_dia != instance.dia_semana:
                diff = instance.dia_semana - t.fecha.isoweekday()
                t.fecha = t.fecha + datetime.timedelta(days=diff)
            
            t.save()
            
        # 2. Also shift any orphaned turnos from old slot to new slot
        if old_dia != instance.dia_semana or old_hora != instance.hora_inicio or old_clase_id != instance.clase_id:
            old_orphans = Turno.objects.filter(
                plantilla__isnull=True,
                clase_id=old_clase_id,
                fecha__gte=now,
                hora_inicio=old_hora
            )
            for t in old_orphans:
                if t.fecha.isoweekday() == old_dia:
                    t.plantilla = instance
                    t.clase = instance.clase
                    t.hora_inicio = instance.hora_inicio
                    t.hora_fin = instance.hora_fin
                    if old_dia != instance.dia_semana:
                        diff = instance.dia_semana - t.fecha.isoweekday()
                        t.fecha = t.fecha + datetime.timedelta(days=diff)
                    t.save()
        
        # 3. Deduplicate
        self._deduplicate_turnos(instance, now)
            
        from backend_core.hooks import registry
        registry.execute("after_plantilla_updated", self.request.data, instance=instance, old_dia=old_dia, old_hora=old_hora, old_clase_id=old_clase_id)
        from .services import generar_turnos_desde_plantillas
        generar_turnos_desde_plantillas()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        from django.utils import timezone
        now = timezone.localdate()
        
        # 1. Fire hook to deactivate recurrencias
        from backend_core.hooks import registry
        registry.execute(
            "after_slot_destroyed", 
            {}, 
            clase_id=instance.clase_id, 
            dia_semana=instance.dia_semana, 
            hora_inicio=instance.hora_inicio
        )
        
        # 2. Delete all future turnos linked to this plantilla
        Turno.objects.filter(
            plantilla=instance,
            fecha__gte=now
        ).delete()
        
        # 3. Also delete any orphaned turnos matching this slot
        target_turnos = Turno.objects.filter(
            clase_id=instance.clase_id,
            fecha__gte=now,
            hora_inicio=instance.hora_inicio
        )
        ids_to_delete = [t.id for t in target_turnos if t.fecha.isoweekday() == instance.dia_semana]
        if ids_to_delete:
            Turno.objects.filter(id__in=ids_to_delete).delete()
            
        return super().destroy(request, *args, **kwargs)


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

    def perform_create(self, serializer):
        user = serializer.save()
        from backend_core.hooks import registry
        registry.execute('post_admin_usuario_save', data=self.request.data, user=user)

    def perform_update(self, serializer):
        user = serializer.save()
        from backend_core.hooks import registry
        registry.execute('post_admin_usuario_save', data=self.request.data, user=user)

    @action(detail=True, methods=['get'])
    def clases(self, request, pk=None):
        usuario = self.get_object()
        from core.models import Reserva
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        reservas = Reserva.objects.filter(usuario=usuario).select_related('turno__clase').order_by('-turno__fecha', '-turno__hora_inicio')
        
        if month and year:
            reservas = reservas.filter(turno__fecha__month=int(month), turno__fecha__year=int(year))
            
        data = []
        for r in reservas:
            t = r.turno
            data.append({
                'id': str(r.id),
                'turno_id': str(t.id),
                'fecha': t.fecha.isoformat(),
                'hora_inicio': t.hora_inicio.strftime('%H:%M'),
                'hora_fin': t.hora_fin.strftime('%H:%M'),
                'clase_nombre': t.clase.nombre,
                'estado': r.estado,
                'es_recurrente': r.es_recurrente
            })
        return Response(data)



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

