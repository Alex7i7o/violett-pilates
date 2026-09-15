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
            return BilleteraCliente.objects.all().order_by('-fecha_compra')
        return BilleteraCliente.objects.filter(usuario=user).order_by('-fecha_compra')
