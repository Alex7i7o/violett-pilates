from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils.dateparse import parse_date
import datetime

from .models import DisponibilidadDia, ReservaEstetica
from .whatsapp_service import notificar_reserva_estetica_creada

from .serializers import DisponibilidadDiaSerializer, ReservaEsteticaSerializer
from plugins.estetica_servicios.backend.models import ServicioEstetica
from plugins.estetica_paquetes.backend.models import BilleteraCliente

class DisponibilidadDiaViewSet(viewsets.ModelViewSet):
    queryset = DisponibilidadDia.objects.all().order_by('dia_semana')
    serializer_class = DisponibilidadDiaSerializer
    permission_classes = [permissions.IsAdminUser]

class ReservaEsteticaViewSet(viewsets.ModelViewSet):
    serializer_class = ReservaEsteticaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.rol == 'ADMIN':
            return ReservaEstetica.objects.all().order_by('fecha', 'hora_inicio')
        return ReservaEstetica.objects.filter(usuario=self.request.user).order_by('fecha', 'hora_inicio')

    def perform_create(self, serializer):
        # Debitar de la billetera si tiene saldo (lógica simple por ahora)
        servicio = serializer.validated_data.get('servicio')
        # Buscar billetera activa
        billetera = BilleteraCliente.objects.filter(
            usuario=self.request.user,
            servicio=servicio,
            estado='ACTIVO',
            sesiones_restantes__gt=0
        ).first()
        
        if not billetera:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'No tienes sesiones disponibles para este servicio. Por favor, adquiere un paquete en la tienda.'})
            
        billetera.sesiones_restantes -= 1
        if billetera.sesiones_restantes == 0:
            billetera.estado = 'AGOTADO'
        billetera.save()
        
        reserva = serializer.save(usuario=self.request.user)
        try:
            notificar_reserva_estetica_creada(self.request.user, reserva)
        except Exception as e:
            print('[WHATSAPP] Error enviando mensaje', e)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_disponibilidad(request):
    fecha_str = request.query_params.get('fecha')
    servicio_id = request.query_params.get('servicio_id')
    
    if not fecha_str or not servicio_id:
        return Response({'error': 'Faltan parámetros fecha y servicio_id'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        fecha = parse_date(fecha_str)
        if not fecha:
            raise ValueError
    except ValueError:
        return Response({'error': 'Formato de fecha inválido (YYYY-MM-DD)'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        servicio = ServicioEstetica.objects.get(id=servicio_id)
    except ServicioEstetica.DoesNotExist:
        return Response({'error': 'Servicio no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
    dia_semana = fecha.weekday()
    try:
        dia_config = DisponibilidadDia.objects.get(dia_semana=dia_semana, is_active=True)
    except DisponibilidadDia.DoesNotExist:
        return Response([]) # No abre ese día
        
    reservas_dia = ReservaEstetica.objects.filter(fecha=fecha).exclude(estado='CANCELADA')
    
    slots = []
    current_time = datetime.datetime.combine(fecha, dia_config.hora_apertura)
    close_time = datetime.datetime.combine(fecha, dia_config.hora_cierre)
    duracion = datetime.timedelta(minutes=servicio.duracion_minutos)
    
    break_start = None
    break_end = None
    if dia_config.break_inicio and dia_config.break_fin:
        break_start = datetime.datetime.combine(fecha, dia_config.break_inicio)
        break_end = datetime.datetime.combine(fecha, dia_config.break_fin)
        
    while current_time + duracion <= close_time:
        slot_end = current_time + duracion
        
        # Check overlaps
        is_break = False
        if break_start and break_end:
            if (current_time < break_end) and (slot_end > break_start):
                is_break = True
                
        is_reserved = False
        for r in reservas_dia:
            r_start = datetime.datetime.combine(fecha, r.hora_inicio)
            r_end = datetime.datetime.combine(fecha, r.hora_fin)
            if (current_time < r_end) and (slot_end > r_start):
                is_reserved = True
                break
                
        if not is_break and not is_reserved:
            slots.append(current_time.strftime('%H:%M'))
            
        current_time += duracion
        
    return Response(slots)
