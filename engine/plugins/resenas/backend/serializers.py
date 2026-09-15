from rest_framework import serializers
from .models import Resena

class ResenaSerializer(serializers.ModelSerializer):
    autor = serializers.SerializerMethodField()

    class Meta:
        model = Resena
        fields = ['id', 'estrellas', 'mensaje', 'fecha', 'autor']
        read_only_fields = ['id', 'fecha', 'autor']

    def get_autor(self, obj):
        return f"{obj.usuario.nombre} {obj.usuario.apellido}"
