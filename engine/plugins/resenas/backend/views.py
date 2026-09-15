from rest_framework import viewsets, permissions
from .models import Resena
from .serializers import ResenaSerializer

class ResenaViewSet(viewsets.ModelViewSet):
    serializer_class = ResenaSerializer

    def get_queryset(self):
        return Resena.objects.all().order_by('-fecha')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
