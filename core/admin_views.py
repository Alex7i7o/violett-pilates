from rest_framework import viewsets, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from django.utils.dateparse import parse_date
import datetime

from .models import Profesor, Turno, Reserva, Usuario, Suscripcion, Plan, ConfiguracionGlobal, PlantillaTurno, Clase
from .serializers import (
    ProfesorSerializer, 
    AdminTurnoSerializer, 
    AdminUsuarioSerializer,
    PlantillaTurnoSerializer,
    ClaseSerializer
)

class IsStaffPermission(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (request.user.is_staff or request.user.rol == 'ADMIN')


from rest_framework import serializers
class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [IsStaffPermission]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.filter(is_active=True)
    serializer_class = ProfesorSerializer
    permission_classes = [IsStaffPermission]

    def perform_create(self, serializer):
        profesor = serializer.save()
        if profesor.email:
            # Check if user already exists
            usuario = Usuario.objects.filter(email=profesor.email).first()
            if not usuario:
                usuario = Usuario.objects.create(
                    email=profesor.email,
                    nombre=profesor.nombre,
                    apellido=profesor.apellido,
                    telefono=profesor.telefono,
                    rol='PROFESOR'
                )
                usuario.set_password('violett123')
                usuario.save()
            
            profesor.usuario = usuario
            profesor.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        if instance.usuario:
            instance.usuario.is_active = False
            instance.usuario.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminAgendaView(views.APIView):
    permission_classes = [IsStaffPermission]

    def get(self, request):
        fecha_str = request.query_params.get('fecha')
        if not fecha_str:
            fecha = timezone.localdate()
        else:
            fecha = parse_date(fecha_str)

        turnos = Turno.objects.select_related('clase', 'profesor').prefetch_related('reservas__usuario').filter(fecha=fecha, estado__in=['PROGRAMADO', 'CONFIRMADO', 'COMPLETADO']).order_by('hora_inicio')
        serializer = AdminTurnoSerializer(turnos, many=True)
        return Response(serializer.data)


class AdminTurnoViewSet(viewsets.ModelViewSet):
    queryset = Turno.objects.all()
    serializer_class = AdminTurnoSerializer
    permission_classes = [IsStaffPermission]

    def destroy(self, request, *args, **kwargs):
        turno = self.get_object()
        reservas = Reserva.objects.select_related('usuario', 'turno').filter(turno=turno, estado='CONFIRMADA')
        for reserva in reservas:
            reserva.estado = 'CANCELADA_TIEMPO'
            reserva.save()
            
            suscripcion = reserva.suscripcion
            suscripcion.clases_restantes += 1
            if suscripcion.estado == 'AGOTADO':
                suscripcion.estado = 'ACTIVO'
            suscripcion.save()
        
        turno.estado = 'CANCELADO'
        turno.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminReservaAsistenciaView(views.APIView):
    permission_classes = [IsStaffPermission]

    def patch(self, request, pk):
        try:
            reserva = Reserva.objects.get(pk=pk)
        except Reserva.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        nuevo_estado = request.data.get('estado')
        if nuevo_estado not in ['TOMADA', 'AUSENTE', 'CONFIRMADA']:
            return Response({"error": "Estado inválido"}, status=status.HTTP_400_BAD_REQUEST)
            
        reserva.estado = nuevo_estado
        reserva.save()
        
        if reserva.turno.estado != 'COMPLETADO':
            reserva.turno.estado = 'COMPLETADO'
            reserva.turno.save()
            
        return Response({"status": "ok", "estado": nuevo_estado})


class AdminAlumnoViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.filter(rol='CLIENTE', is_active=True).order_by('nombre')
    serializer_class = AdminUsuarioSerializer
    permission_classes = [IsStaffPermission]

    def perform_create(self, serializer):
        user = serializer.save(rol='CLIENTE')
        user.set_password('violett123')
        user.save()

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(telefono__icontains=q))
        return qs

    @action(detail=True, methods=['post'], url_path='asignar-plan')
    def asignar_plan(self, request, pk=None):
        alumno = self.get_object()
        plan_id = request.data.get('plan_id')
        
        try:
            plan = Plan.objects.get(id=plan_id)
        except Plan.DoesNotExist:
            return Response({"error": "Plan no encontrado"}, status=status.HTTP_404_NOT_FOUND)
            
        Suscripcion.objects.filter(usuario=alumno, estado__in=['ACTIVO', 'AGOTADO']).update(estado='VENCIDO')
        
        from django.utils import timezone
        
        config = ConfiguracionGlobal.objects.first()
        dias = config.dias_vencimiento_plan if config else 30
        
        fecha_inicio = timezone.localdate()
        fecha_vencimiento = fecha_inicio + datetime.timedelta(days=dias)
        
        nueva_sub = Suscripcion.objects.create(
            usuario=alumno,
            plan=plan,
            clases_restantes=plan.cantidad_clases,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            estado='ACTIVO'
        )
        return Response({"status": "ok", "suscripcion_id": nueva_sub.id})

class PlantillaTurnoViewSet(viewsets.ModelViewSet):
    queryset = PlantillaTurno.objects.select_related('clase', 'profesor').filter(is_active=True)
    serializer_class = PlantillaTurnoSerializer
    permission_classes = [IsStaffPermission]

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_dia = old_instance.dia_semana
        old_inicio = old_instance.hora_inicio
        old_fin = old_instance.hora_fin
        
        instance = serializer.save()
        
        from django.utils import timezone
        from django.core.mail import send_mail
        from core.models import Reserva, Recurrencia
        
        if old_dia != instance.dia_semana or old_inicio != instance.hora_inicio or old_fin != instance.hora_fin:
            today = timezone.localdate()
            turnos_futuros = instance.turnos_generados.filter(fecha__gte=today, estado='PROGRAMADO')
            
            # Actualizar recurrencias asociadas a este horario
            recurrencias = Recurrencia.objects.filter(
                clase=instance.clase,
                dia_semana=old_dia,
                hora_inicio=old_inicio,
                is_active=True
            )
            
            for rec in recurrencias:
                if old_dia != instance.dia_semana:
                    # Cancelar la recurrencia porque cambió el día
                    rec.is_active = False
                    rec.save()
                    send_mail(
                        'Horario fijo cancelado por cambio de día',
                        f'Hola {rec.usuario.nombre},\n\nEl horario fijo que tenías para {instance.clase.nombre} ha cambiado de día. Tu turno fijo ha sido dado de baja. Por favor, ingresa al sistema para elegir un nuevo horario.\n\nSaludos,\nViolett Pilates',
                        'no-reply@violettpilates.com',
                        [rec.usuario.email],
                        fail_silently=True,
                    )
                else:
                    # Solo cambió la hora, la mantenemos
                    rec.hora_inicio = instance.hora_inicio
                    rec.save()
                    send_mail(
                        'Cambio de hora de tu horario fijo',
                        f'Hola {rec.usuario.nombre},\n\nTu horario fijo de {instance.clase.nombre} ha cambiado su horario. Ahora será a las {instance.hora_inicio.strftime("%H:%M")}.\n\nSaludos,\nViolett Pilates',
                        'no-reply@violettpilates.com',
                        [rec.usuario.email],
                        fail_silently=True,
                    )

            # Actualizar turnos futuros
            for turno in turnos_futuros:
                if old_dia != instance.dia_semana:
                    turno.estado = 'CANCELADO'
                    turno.save()
                    reservas = Reserva.objects.filter(turno=turno, estado='CONFIRMADA')
                    for reserva in reservas:
                        reserva.estado = 'CANCELADA'
                        reserva.save()
                        if reserva.usuario.suscripcion_activa:
                            reserva.usuario.suscripcion_activa.clases_disponibles += 1
                            reserva.usuario.suscripcion_activa.save()
                        
                        send_mail(
                            'Cambio de día de tu clase',
                            f'Hola {reserva.usuario.nombre},\n\nLa clase puntual de {instance.clase.nombre} del {turno.fecha} ha cambiado de día y tu reserva fue cancelada. Te devolvimos el crédito.\n\nSaludos,\nViolett Pilates',
                            'no-reply@violettpilates.com',
                            [reserva.usuario.email],
                            fail_silently=True,
                        )
                else:
                    turno.hora_inicio = instance.hora_inicio
                    turno.hora_fin = instance.hora_fin
                    turno.save()
                    reservas = Reserva.objects.filter(turno=turno, estado='CONFIRMADA')
                    for reserva in reservas:
                        send_mail(
                            'Cambio de horario de tu clase',
                            f'Hola {reserva.usuario.nombre},\n\nLa clase de {instance.clase.nombre} del {turno.fecha} cambió de horario. Ahora será de {instance.hora_inicio.strftime("%H:%M")} a {instance.hora_fin.strftime("%H:%M")}.\n\nSaludos,\nViolett Pilates',
                            'no-reply@violettpilates.com',
                            [reserva.usuario.email],
                            fail_silently=True,
                        )

    def perform_destroy(self, instance):
        from django.utils import timezone
        from django.core.mail import send_mail
        from core.models import Reserva, Recurrencia
        
        # Cancelar recurrencias
        recurrencias = Recurrencia.objects.filter(
            clase=instance.clase,
            dia_semana=instance.dia_semana,
            hora_inicio=instance.hora_inicio,
            is_active=True
        )
        for rec in recurrencias:
            rec.is_active = False
            rec.save()
            send_mail(
                'Horario fijo cancelado',
                f'Hola {rec.usuario.nombre},\n\nEl horario fijo que tenías para {instance.clase.nombre} ha sido eliminado del sistema de forma definitiva. Tu turno fijo fue dado de baja.\n\nSaludos,\nViolett Pilates',
                'no-reply@violettpilates.com',
                [rec.usuario.email],
                fail_silently=True,
            )

        today = timezone.localdate()
        turnos_futuros = instance.turnos_generados.filter(fecha__gte=today, estado='PROGRAMADO')
        
        for turno in turnos_futuros:
            turno.estado = 'CANCELADO'
            turno.save()
            reservas = Reserva.objects.filter(turno=turno, estado='CONFIRMADA')
            for reserva in reservas:
                reserva.estado = 'CANCELADA'
                reserva.save()
                if reserva.usuario.suscripcion_activa:
                    reserva.usuario.suscripcion_activa.clases_disponibles += 1
                    reserva.usuario.suscripcion_activa.save()
                
                send_mail(
                    'Clase cancelada',
                    f'Hola {reserva.usuario.nombre},\n\nLamentamos informarte que la clase de {instance.clase.nombre} del {turno.fecha} ha sido cancelada. Te devolvimos el crédito.\n\nSaludos,\nViolett Pilates',
                    'no-reply@violettpilates.com',
                    [reserva.usuario.email],
                    fail_silently=True,
                )
        
        instance.is_active = False
        instance.save()


class ClaseViewSet(viewsets.ModelViewSet):
    queryset = Clase.objects.filter(is_active=True)
    serializer_class = ClaseSerializer
    permission_classes = [IsStaffPermission]
