from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import ReglaPaquete, BilleteraCliente
from .serializers import ReglaPaqueteSerializer, BilleteraClienteSerializer


class ReglaPaqueteViewSet(viewsets.ModelViewSet):
    queryset = ReglaPaquete.objects.all().order_by('cantidad_sesiones')
    serializer_class = ReglaPaqueteSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class BilleteraClienteViewSet(viewsets.ModelViewSet):
    serializer_class = BilleteraClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'ADMIN':
            qs = BilleteraCliente.objects.select_related('usuario', 'servicio').order_by('-fecha_compra')
            usuario_id = self.request.query_params.get('usuario')
            if usuario_id:
                qs = qs.filter(usuario_id=usuario_id)
            return qs
        return BilleteraCliente.objects.select_related('usuario', 'servicio').filter(usuario=user).order_by('-fecha_compra')

    def perform_create(self, serializer):
        sesiones_restantes = serializer.validated_data.get('sesiones_restantes', 0)
        estado = serializer.validated_data.get('estado', 'ACTIVO')
        if sesiones_restantes <= 0:
            estado = 'AGOTADO'
        elif estado == 'AGOTADO' and sesiones_restantes > 0:
            estado = 'ACTIVO'
        serializer.save(estado=estado)

    def perform_update(self, serializer):
        instance = self.get_object()
        sesiones_restantes = serializer.validated_data.get('sesiones_restantes', instance.sesiones_restantes)
        sesiones_totales = serializer.validated_data.get('sesiones_totales', instance.sesiones_totales)
        if sesiones_restantes > sesiones_totales:
            sesiones_totales = sesiones_restantes
        estado = serializer.validated_data.get('estado', instance.estado)
        if sesiones_restantes <= 0:
            sesiones_restantes = 0
            estado = 'AGOTADO'
        elif estado == 'AGOTADO' and sesiones_restantes > 0:
            estado = 'ACTIVO'
        serializer.save(
            sesiones_restantes=sesiones_restantes,
            sesiones_totales=sesiones_totales,
            estado=estado
        )
