from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Plan, Suscripcion
from .serializers import PlanSerializer, SuscripcionSerializer
from django.utils import timezone
from core.models import Usuario

class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
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

        # Cancel any active subscription
        active_subs = Suscripcion.objects.filter(usuario=usuario, estado='ACTIVO')
        for sub in active_subs:
            sub.estado = 'VENCIDO'
            sub.save()

                # Create new subscription
        import datetime
        nueva_suscripcion = Suscripcion.objects.create(
            usuario=usuario,
            plan=plan,
            clases_restantes=plan.cantidad_clases,
            fecha_inicio=timezone.localdate(),
            fecha_vencimiento=timezone.localdate() + datetime.timedelta(days=30),
            estado='ACTIVO'
        )

        return Response({'detail': 'Plan asignado correctamente'})
