from django.db import transaction
from core.models import Reserva, Turno
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

        # Cantidad de clases / créditos iniciales a cargar (permite override del admin)
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

        auto_agendar = request.data.get('auto_agendar', True)
        if isinstance(auto_agendar, str):
            auto_agendar = auto_agendar.lower() in ['true', '1', 'yes']

        # Cancel any active or exhausted subscription
        Suscripcion.objects.filter(usuario=usuario, estado__in=['ACTIVO', 'AGOTADO']).update(estado='VENCIDO')

        # Create new subscription
        nueva_suscripcion = Suscripcion.objects.create(
            usuario=usuario,
            plan=plan,
            clases_restantes=clases_a_cargar,
            fecha_inicio=today,
            fecha_vencimiento=fecha_vencimiento,
            estado='ACTIVO' if clases_a_cargar > 0 else 'AGOTADO'
        )
        
        from backend_core.hooks import registry
        registry.execute('plan_asignado', data={'suscripcion': nueva_suscripcion, 'usuario': usuario, 'plan': plan})

        # Auto-agendar en turnos fijos (recurrencias) si existen y está activado
        reservas_agendadas = 0
        if auto_agendar and clases_a_cargar > 0:
            try:
                from plugins.recurrencias.backend.services import auto_agendar_recurrencias_usuario
                reservas_agendadas = auto_agendar_recurrencias_usuario(usuario, nueva_suscripcion)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error auto-agendando en asignar-plan: {e}")

        nueva_suscripcion.refresh_from_db()

        return Response({
            'detail': 'Plan asignado correctamente',
            'clases_cargadas': clases_a_cargar,
            'clases_restantes': nueva_suscripcion.clases_restantes,
            'clases_agendadas': reservas_agendadas,
            'fecha_vencimiento': nueva_suscripcion.fecha_vencimiento.strftime("%Y-%m-%d"),
            'estado': nueva_suscripcion.estado
        })


class CancelarPlanView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, usuario_id):
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        cancelar_reservas = request.data.get('cancelar_reservas_futuras', True)
        if isinstance(cancelar_reservas, str):
            cancelar_reservas = cancelar_reservas.lower() in ['true', '1', 'yes']

        subs = Suscripcion.objects.filter(usuario=usuario, estado__in=['ACTIVO', 'AGOTADO'])
        if not subs.exists():
            return Response({'detail': 'El alumno no tiene ningún plan activo para cancelar.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            subs.update(estado='CANCELADO', clases_restantes=0)

            reservas_canceladas = 0
            if cancelar_reservas:
                today = timezone.localdate()
                futuras = Reserva.objects.filter(
                    usuario=usuario,
                    turno__fecha__gte=today,
                    estado='CONFIRMADA'
                ).select_related('turno')

                from backend_core.hooks import registry
                from plugins.membresias.backend.models import ReservaMembresia

                for r in futuras:
                    r.estado = 'CANCELADA_TIEMPO'
                    r.save()
                    turno = r.turno
                    turno.cupo_actual += 1
                    turno.save()
                    ReservaMembresia.objects.filter(reserva=r).delete()
                    try:
                        registry.execute('reserva_cancelada_a_tiempo', r)
                    except Exception:
                        pass
                    reservas_canceladas += 1

        return Response({
            'detail': 'Plan cancelado correctamente.',
            'reservas_canceladas': reservas_canceladas
        })


class CancelarClasesFuturasView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, usuario_id):
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        devolver_creditos = request.data.get('devolver_creditos', False)
        if isinstance(devolver_creditos, str):
            devolver_creditos = devolver_creditos.lower() in ['true', '1', 'yes']

        cantidad = request.data.get('cantidad')
        reserva_ids = request.data.get('reserva_ids')
        today = timezone.localdate()

        futuras_qs = Reserva.objects.filter(
            usuario=usuario,
            turno__fecha__gte=today,
            estado='CONFIRMADA'
        ).select_related('turno').order_by('-turno__fecha', '-turno__hora_inicio')

        if reserva_ids:
            futuras = list(futuras_qs.filter(id__in=reserva_ids))
        elif cantidad is not None:
            try:
                cnt = int(cantidad)
                futuras = list(futuras_qs[:cnt])
            except (ValueError, TypeError):
                futuras = list(futuras_qs)
        else:
            futuras = list(futuras_qs)

        if not futuras:
            return Response({'detail': 'No hay clases futuras confirmadas para cancelar.', 'canceladas': 0})

        sub = Suscripcion.objects.filter(usuario=usuario, estado__in=['ACTIVO', 'AGOTADO']).first()
        from backend_core.hooks import registry
        from plugins.membresias.backend.models import ReservaMembresia

        canceladas = 0
        with transaction.atomic():
            for r in futuras:
                r.estado = 'CANCELADA_TIEMPO'
                r.save()
                turno = r.turno
                turno.cupo_actual += 1
                turno.save()
                ReservaMembresia.objects.filter(reserva=r).delete()

                if devolver_creditos and sub:
                    sub.clases_restantes += 1
                    if sub.estado == 'AGOTADO':
                        sub.estado = 'ACTIVO'

                try:
                    registry.execute('reserva_cancelada_a_tiempo', r)
                except Exception:
                    pass
                canceladas += 1

            if sub and devolver_creditos:
                sub.save()

        return Response({
            'detail': f'Se cancelaron {canceladas} clases futuras.',
            'canceladas': canceladas,
            'clases_restantes': sub.clases_restantes if sub else 0
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
