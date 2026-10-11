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

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if self.action in ['update', 'partial_update', 'destroy']:
            if obj.usuario != request.user and request.user.rol != 'ADMIN':
                self.permission_denied(request, message="No tienes permiso para modificar esta reseña.")

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
