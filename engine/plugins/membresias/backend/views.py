from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Plan, Suscripcion
from .serializers import PlanSerializer, SuscripcionSerializer
from django.utils import timezone
from core.models import Usuario
import datetime

class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    
    def get_permissions(self):
        from rest_framework.permissions import AllowAny
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class SuscripcionViewSet(viewsets.ModelViewSet):
    queryset = Suscripcion.objects.all()
    serializer_class = SuscripcionSerializer
    permission_classes = [IsAdminUser]

class AsignarPlanView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, usuario_id):
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({'detail': 'Falta plan_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
            usuario = Usuario.objects.get(id=usuario_id)
        except Plan.DoesNotExist:
            return Response({'detail': 'Plan no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Cancel any active or exhausted subscription
        Suscripcion.objects.filter(usuario=usuario, estado__in=['ACTIVO', 'AGOTADO']).update(estado='VENCIDO')

        # Create new subscription
        today = timezone.localdate()
        nueva_suscripcion = Suscripcion.objects.create(
            usuario=usuario,
            plan=plan,
            clases_restantes=plan.cantidad_clases,
            fecha_inicio=today,
            fecha_vencimiento=today + datetime.timedelta(days=30),
            estado='ACTIVO'
        )
        
        from backend_core.hooks import registry
        registry.execute('plan_asignado', data={'suscripcion': nueva_suscripcion, 'usuario': usuario, 'plan': plan})

        # Auto-agendar en turnos fijos (recurrencias) si existen
        reservas_agendadas = 0
        try:
            from plugins.recurrencias.backend.services import auto_agendar_recurrencias_usuario
            reservas_agendadas = auto_agendar_recurrencias_usuario(usuario, nueva_suscripcion)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error auto-agendando en asignar-plan: {e}")

        nueva_suscripcion.refresh_from_db()

        return Response({
            'detail': 'Plan asignado correctamente',
            'clases_cargadas': plan.cantidad_clases,
            'clases_restantes': nueva_suscripcion.clases_restantes,
            'clases_agendadas': reservas_agendadas,
            'fecha_vencimiento': nueva_suscripcion.fecha_vencimiento.strftime("%Y-%m-%d"),
            'estado': nueva_suscripcion.estado
        })


class ReactivarPlanView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, usuario_id):
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        plan_id = request.data.get('plan_id')
        plan = None
        if plan_id:
            try:
                plan = Plan.objects.get(id=plan_id, is_active=True)
            except Plan.DoesNotExist:
                return Response({'detail': 'Plan especificado no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        else:
            ultima_sub = Suscripcion.objects.filter(usuario=usuario).order_by('-fecha_inicio').first()
            if ultima_sub:
                plan = ultima_sub.plan
            else:
                return Response({
                    'detail': 'El alumno no tiene ningún plan previo para reactivar. Por favor seleccione un plan.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Cantidad de clases a cargar
        clases_input = request.data.get('clases')
        if clases_input is not None:
            try:
                clases_a_cargar = int(clases_input)
            except (ValueError, TypeError):
                clases_a_cargar = plan.cantidad_clases
        else:
            clases_a_cargar = plan.cantidad_clases

        # Fecha de vencimiento
        today = timezone.localdate()
        vencimiento_input = request.data.get('fecha_vencimiento')
        if vencimiento_input:
            try:
                fecha_vencimiento = datetime.date.fromisoformat(str(vencimiento_input))
            except Exception:
                fecha_vencimiento = today + datetime.timedelta(days=30)
        else:
            fecha_vencimiento = today + datetime.timedelta(days=30)

        # Vencer suscripciones anteriores
        Suscripcion.objects.filter(usuario=usuario, estado__in=['ACTIVO', 'AGOTADO']).update(estado='VENCIDO')

        # Crear nueva suscripción activa
        nueva_suscripcion = Suscripcion.objects.create(
            usuario=usuario,
            plan=plan,
            clases_restantes=clases_a_cargar,
            fecha_inicio=today,
            fecha_vencimiento=fecha_vencimiento,
            estado='ACTIVO'
        )

        # Disparar hook de asignación de plan
        from backend_core.hooks import registry
        registry.execute('plan_asignado', data={'suscripcion': nueva_suscripcion, 'usuario': usuario, 'plan': plan})

        # Auto-agendar en turnos fijos (recurrencias) si el parámetro auto_agendar es True
        reservas_agendadas = 0
        if request.data.get('auto_agendar', True):
            try:
                from plugins.recurrencias.backend.services import auto_agendar_recurrencias_usuario
                reservas_agendadas = auto_agendar_recurrencias_usuario(usuario, nueva_suscripcion)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error auto-agendando recurrencias al reactivar: {e}")

        nueva_suscripcion.refresh_from_db()

        return Response({
            'detail': f'Plan "{plan.nombre}" reactivado exitosamente.',
            'plan_nombre': plan.nombre,
            'clases_cargadas': clases_a_cargar,
            'clases_restantes': nueva_suscripcion.clases_restantes,
            'clases_agendadas': reservas_agendadas,
            'fecha_vencimiento': nueva_suscripcion.fecha_vencimiento.strftime("%Y-%m-%d"),
            'estado': nueva_suscripcion.estado
        }, status=status.HTTP_200_OK)
