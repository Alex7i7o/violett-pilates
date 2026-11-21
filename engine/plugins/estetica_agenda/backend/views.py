import datetime
from django.utils.dateparse import parse_date, parse_time
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.models import Usuario
from .models import DisponibilidadDia, ReservaEstetica
from .whatsapp_service import notificar_reserva_estetica_creada
from .google_calendar_service import (
    crear_evento_calendario,
    actualizar_evento_calendario,
    cancelar_evento_calendario,
    consultar_ocupados_google,
)
from .serializers import DisponibilidadDiaSerializer, ReservaEsteticaSerializer
from plugins.estetica_servicios.backend.models import ServicioEstetica
from plugins.estetica_paquetes.backend.models import BilleteraCliente


def calcular_hora_fin(fecha: datetime.date, hora_inicio: datetime.time, duracion_minutos: int) -> datetime.time:
    dt_inicio = datetime.datetime.combine(fecha, hora_inicio)
    dt_fin = dt_inicio + datetime.timedelta(minutes=duracion_minutos)
    return dt_fin.time()


def verificar_solapamiento(fecha: datetime.date, hora_inicio: datetime.time, hora_fin: datetime.time, exclude_id=None) -> bool:
    qs = ReservaEstetica.objects.filter(fecha=fecha).exclude(estado='CANCELADA')
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    start_dt = datetime.datetime.combine(fecha, hora_inicio)
    end_dt = datetime.datetime.combine(fecha, hora_fin)
    for r in qs:
        r_start = datetime.datetime.combine(fecha, r.hora_inicio)
        r_end = datetime.datetime.combine(fecha, r.hora_fin)
        if r_end <= r_start:
            r_end = r_start + datetime.timedelta(minutes=r.servicio.duracion_minutos)
        if (start_dt < r_end) and (end_dt > r_start):
            return True
    return False


def devolver_sesion_billetera(usuario, servicio) -> bool:
    billetera = BilleteraCliente.objects.filter(
        usuario=usuario,
        servicio=servicio,
        estado__in=['ACTIVO', 'AGOTADO']
    ).order_by('-fecha_compra').first()
    if not billetera:
        return False
    billetera.sesiones_restantes += 1
    if billetera.sesiones_restantes > billetera.sesiones_totales:
        billetera.sesiones_totales = billetera.sesiones_restantes
    if billetera.sesiones_restantes > 0 and billetera.estado == 'AGOTADO':
        billetera.estado = 'ACTIVO'
    billetera.save()
    return True


class DisponibilidadDiaViewSet(viewsets.ModelViewSet):
    queryset = DisponibilidadDia.objects.all().order_by('dia_semana')
    serializer_class = DisponibilidadDiaSerializer
    permission_classes = [permissions.IsAdminUser]


class ReservaEsteticaViewSet(viewsets.ModelViewSet):
    serializer_class = ReservaEsteticaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = ReservaEstetica.objects.select_related('usuario', 'servicio').order_by('fecha', 'hora_inicio')
        if self.request.user.rol != 'ADMIN':
            qs = qs.filter(usuario=self.request.user)
        else:
            usuario_id = self.request.query_params.get('usuario')
            if usuario_id:
                qs = qs.filter(usuario_id=usuario_id)

        fecha = self.request.query_params.get('fecha')
        if fecha:
            qs = qs.filter(fecha=fecha)

        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        servicio_id = self.request.query_params.get('servicio')
        if servicio_id:
            qs = qs.filter(servicio_id=servicio_id)

        return qs

    def perform_create(self, serializer):
        servicio = serializer.validated_data.get('servicio')
        fecha = serializer.validated_data.get('fecha')
        hora_inicio = serializer.validated_data.get('hora_inicio')
        hora_fin = serializer.validated_data.get('hora_fin')

        if not hora_fin or hora_fin <= hora_inicio:
            hora_fin = calcular_hora_fin(fecha, hora_inicio, servicio.duracion_minutos)

        if verificar_solapamiento(fecha, hora_inicio, hora_fin):
            raise ValidationError({'detail': 'El horario seleccionado ya se encuentra ocupado por otro turno.'})

        is_admin = self.request.user.rol == 'ADMIN'
        target_user = self.request.user
        if is_admin:
            explicit_user = serializer.validated_data.get('usuario')
            usuario_id_param = self.request.data.get('usuario_id') or self.request.data.get('usuario')
            if explicit_user:
                target_user = explicit_user
            elif usuario_id_param:
                try:
                    target_user = Usuario.objects.get(id=usuario_id_param)
                except Usuario.DoesNotExist:
                    raise ValidationError({'detail': 'El paciente seleccionado no existe.'})

        descontar_raw = self.request.data.get('descontar_credito', True)
        descontar_credito = descontar_raw not in [False, 'false', 'False', '0', 0] if is_admin else True

        if descontar_credito:
            billetera = BilleteraCliente.objects.filter(
                usuario=target_user,
                servicio=servicio,
                estado='ACTIVO',
                sesiones_restantes__gt=0
            ).order_by('fecha_vencimiento', 'fecha_compra').first()

            if not billetera:
                if is_admin:
                    raise ValidationError({
                        'detail': 'El paciente no tiene sesiones disponibles en su billetera para este servicio. Podés acreditarle sesiones desde su ficha o desmarcar "Descontar sesión de billetera".'
                    })
                raise ValidationError({
                    'detail': 'No tienes sesiones disponibles para este servicio. Por favor, adquiere un paquete en la tienda.'
                })

            billetera.sesiones_restantes -= 1
            if billetera.sesiones_restantes <= 0:
                billetera.sesiones_restantes = 0
                billetera.estado = 'AGOTADO'
            billetera.save()

        reserva = serializer.save(usuario=target_user, hora_fin=hora_fin)

        # Sincronización en segundo plano con Google Calendar (sin romper si falla conexión externa)
        try:
            event_id = crear_evento_calendario(reserva)
            if event_id:
                reserva.google_event_id = event_id
                reserva.save(update_fields=['google_event_id'])
        except Exception as e:
            print('[GOOGLE CALENDAR] Error sincronizando creación de turno:', e)

        # Notificación WhatsApp
        try:
            notificar_reserva_estetica_creada(target_user, reserva)
        except Exception as e:
            print('[WHATSAPP] Error enviando mensaje', e)

    def perform_update(self, serializer):
        instance = self.get_object()
        old_estado = instance.estado

        servicio = serializer.validated_data.get('servicio', instance.servicio)
        fecha = serializer.validated_data.get('fecha', instance.fecha)
        hora_inicio = serializer.validated_data.get('hora_inicio', instance.hora_inicio)
        hora_fin = serializer.validated_data.get('hora_fin')
        new_estado = serializer.validated_data.get('estado', instance.estado)

        if not hora_fin or hora_fin <= hora_inicio or hora_inicio != instance.hora_inicio or servicio != instance.servicio:
            hora_fin = calcular_hora_fin(fecha, hora_inicio, servicio.duracion_minutos)

        if new_estado != 'CANCELADA' and (fecha != instance.fecha or hora_inicio != instance.hora_inicio):
            if verificar_solapamiento(fecha, hora_inicio, hora_fin, exclude_id=instance.id):
                raise ValidationError({'detail': 'El nuevo horario seleccionado ya se encuentra ocupado.'})

        reserva = serializer.save(hora_fin=hora_fin)

        # Sincronización con Google Calendar
        try:
            actualizar_evento_calendario(reserva)
        except Exception as e:
            print('[GOOGLE CALENDAR] Error actualizando turno en Calendar:', e)

        devolver_raw = self.request.data.get('devolver_credito', False)
        devolver_credito = devolver_raw in [True, 'true', 'True', '1', 1]
        if old_estado != 'CANCELADA' and new_estado == 'CANCELADA' and devolver_credito:
            devolver_sesion_billetera(reserva.usuario, reserva.servicio)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        if reserva.estado == 'CANCELADA':
            return Response({'detail': 'Este turno ya se encuentra cancelado.'}, status=status.HTTP_400_BAD_REQUEST)

        is_admin = request.user.rol == 'ADMIN'
        devolver_raw = request.data.get('devolver_credito', True)
        devolver_credito = devolver_raw not in [False, 'false', 'False', '0', 0]

        credito_devuelto = False
        if devolver_credito:
            credito_devuelto = devolver_sesion_billetera(reserva.usuario, reserva.servicio)

        reserva.estado = 'CANCELADA'
        reserva.save()

        # Eliminar/Actualizar evento en Google Calendar
        try:
            cancelar_evento_calendario(reserva)
        except Exception as e:
            print('[GOOGLE CALENDAR] Error cancelando evento:', e)

        data = self.get_serializer(reserva).data
        data['credito_devuelto'] = credito_devuelto
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reprogramar(self, request, pk=None):
        reserva = self.get_object()
        if reserva.estado == 'CANCELADA':
            return Response({'detail': 'No se puede reprogramar un turno cancelado.'}, status=status.HTTP_400_BAD_REQUEST)

        fecha_str = request.data.get('fecha')
        hora_str = request.data.get('hora_inicio')
        if not fecha_str or not hora_str:
            return Response({'detail': 'Debes indicar la nueva fecha y hora_inicio.'}, status=status.HTTP_400_BAD_REQUEST)

        nueva_fecha = parse_date(str(fecha_str))
        if len(str(hora_str)) == 5:
            hora_str = f"{hora_str}:00"
        nueva_hora = parse_time(str(hora_str))

        if not nueva_fecha or not nueva_hora:
            return Response({'detail': 'Formato de fecha u hora inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        nueva_hora_fin = calcular_hora_fin(nueva_fecha, nueva_hora, reserva.servicio.duracion_minutos)

        if verificar_solapamiento(nueva_fecha, nueva_hora, nueva_hora_fin, exclude_id=reserva.id):
            return Response({'detail': 'El horario seleccionado ya se encuentra ocupado.'}, status=status.HTTP_400_BAD_REQUEST)

        reserva.fecha = nueva_fecha
        reserva.hora_inicio = nueva_hora
        reserva.hora_fin = nueva_hora_fin
        reserva.estado = 'CONFIRMADA'
        reserva.save()

        # Sincronizar nueva fecha y hora con Google Calendar
        try:
            actualizar_evento_calendario(reserva)
        except Exception as e:
            print('[GOOGLE CALENDAR] Error reprogramando evento:', e)

        return Response(self.get_serializer(reserva).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_disponibilidad(request):
    fecha_str = request.query_params.get('fecha')
    servicio_id = request.query_params.get('servicio_id')
    exclude_reserva_id = request.query_params.get('exclude_reserva_id')

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
        return Response([])  # No abre ese día

    reservas_dia = ReservaEstetica.objects.filter(fecha=fecha).exclude(estado='CANCELADA')
    if exclude_reserva_id:
        reservas_dia = reservas_dia.exclude(id=exclude_reserva_id)

    # Consultar eventos bloqueados de Google Calendar (FreeBusy)
    ocupados_google = []
    try:
        ocupados_google = consultar_ocupados_google(fecha)
    except Exception as e:
        print('[GOOGLE CALENDAR] Error consultando FreeBusy:', e)

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
        slot_start_time = current_time.time()
        slot_end_time = slot_end.time()

        # Check breaks
        is_break = False
        if break_start and break_end:
            if (current_time < break_end) and (slot_end > break_start):
                is_break = True

        # Check local DB bookings
        is_reserved = False
        for r in reservas_dia:
            r_start = datetime.datetime.combine(fecha, r.hora_inicio)
            r_end = datetime.datetime.combine(fecha, r.hora_fin)
            if r_end <= r_start:
                r_end = r_start + datetime.timedelta(minutes=r.servicio.duracion_minutos)
            if (current_time < r_end) and (slot_end > r_start):
                is_reserved = True
                break

        # Check Google Calendar FreeBusy
        is_google_busy = False
        for g_start, g_end in ocupados_google:
            if (slot_start_time < g_end) and (slot_end_time > g_start):
                is_google_busy = True
                break

        if not is_break and not is_reserved and not is_google_busy:
            slots.append(current_time.strftime('%H:%M'))

        current_time += duracion

    return Response(slots)
