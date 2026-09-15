from rest_framework import serializers
from .models import Recurrencia

class RecurrenciaSerializer(serializers.ModelSerializer):
    clase_nombre = serializers.CharField(source='clase.nombre', read_only=True)
    class Meta:
        model = Recurrencia
        fields = '__all__'
