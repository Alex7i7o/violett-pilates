from rest_framework import serializers
from .models import ReglaPaquete, BilleteraCliente

class ReglaPaqueteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReglaPaquete
        fields = '__all__'

class BilleteraClienteSerializer(serializers.ModelSerializer):
    servicio_detalle = serializers.SerializerMethodField()
    usuario_detalle = serializers.SerializerMethodField()
    
    class Meta:
        model = BilleteraCliente
        fields = '__all__'
        
    def get_servicio_detalle(self, obj):
        return {
            'id': str(obj.servicio.id),
            'nombre': obj.servicio.nombre
        }
        
    def get_usuario_detalle(self, obj):
        return {
            'id': str(obj.usuario.id),
            'email': obj.usuario.email,
            'nombre': obj.usuario.nombre,
            'apellido': obj.usuario.apellido
        }
