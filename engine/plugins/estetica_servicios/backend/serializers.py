from rest_framework import serializers
from .models import ServicioEstetica

class ServicioEsteticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicioEstetica
        fields = '__all__'
