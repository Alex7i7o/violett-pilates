from rest_framework import viewsets, permissions
from .models import ServicioEstetica
from .serializers import ServicioEsteticaSerializer

class ServicioEsteticaViewSet(viewsets.ModelViewSet):
    queryset = ServicioEstetica.objects.all().order_by('nombre')
    serializer_class = ServicioEsteticaSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
