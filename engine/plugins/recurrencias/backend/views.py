from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from django.utils import timezone
from .models import Recurrencia
from core.models import Reserva

class CancelRecurrenciaView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        recurrencia_id = request.data.get('id')
        if not recurrencia_id:
            return Response({"detail": "El id de recurrencia es requerido."}, status=status.HTTP_400_BAD_REQUEST)
            
        user = request.user
        
        try:
            recurrencia = Recurrencia.objects.get(id=recurrencia_id, usuario=user, is_active=True)
        except Recurrencia.DoesNotExist:
            return Response({"detail": "Horario fijo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
        recurrencia.is_active = False
        recurrencia.save()
        
        # Cancel all future confirmed reservations for this recurrencia
        reservas = Reserva.objects.filter(
            usuario=user,
            turno__clase=recurrencia.clase,
            turno__fecha__gte=timezone.localdate(),
            turno__hora_inicio=recurrencia.hora_inicio,
            estado='CONFIRMADA',
            es_recurrente=True
        )
        
        for reserva in reservas:
            reserva.estado = 'CANCELADA_TIEMPO'
            reserva.save()
            
            turno = reserva.turno
            turno.cupo_actual += 1
            turno.save()
            

            try:
                rm = reserva.consumo_suscripcion
                suscripcion = rm.suscripcion
                rm.delete()
            except Exception:
                suscripcion = None
            if suscripcion:
                suscripcion.clases_restantes += 1
                if suscripcion.estado == 'AGOTADO':
                    suscripcion.estado = 'ACTIVO'
                suscripcion.save()
            
        return Response({"detail": "Horario fijo cancelado exitosamente."})

class AdminRecurrenciaView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, usuario_id):
        # List recurrencias for a specific user
        recurrencias = Recurrencia.objects.filter(usuario_id=usuario_id, is_active=True).select_related('clase')
        data = []
        for r in recurrencias:
            data.append({
                'id': str(r.id),
                'clase_nombre': r.clase.nombre,
                'clase_id': str(r.clase.id),
                'dia_semana': r.dia_semana,
                'hora_inicio': str(r.hora_inicio)[:5],
            })
        return Response(data)

    def post(self, request, usuario_id):
        # Create a new recurrencia for this user manually
        clase_id = request.data.get('clase_id')
        dia_semana = request.data.get('dia_semana')
        hora_inicio = request.data.get('hora_inicio')
        
        if not all([clase_id, dia_semana, hora_inicio]):
            return Response({"detail": "Faltan datos obligatorios"}, status=400)
            
        from django.contrib.auth import get_user_model
        Usuario = get_user_model()
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except:
            return Response({"detail": "Usuario no encontrado"}, status=404)
            
        # Check if already exists
        exists = Recurrencia.objects.filter(
            usuario=usuario, 
            clase_id=clase_id, 
            dia_semana=dia_semana, 
            hora_inicio=hora_inicio, 
            is_active=True
        ).exists()
        
        if exists:
            return Response({"detail": "El alumno ya tiene este horario fijo asignado"}, status=400)
            
        r = Recurrencia.objects.create(
            usuario=usuario,
            clase_id=clase_id,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            is_active=True
        )

        try:
            from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
            suscripcion = Suscripcion.objects.filter(usuario=usuario, estado='ACTIVO', clases_restantes__gt=0).first()
            if suscripcion:
                from core.models import Turno, Reserva
                from django.utils import timezone
                future_turnos = Turno.objects.filter(clase_id=clase_id, hora_inicio=hora_inicio, fecha__gte=timezone.localdate(), fecha__lte=suscripcion.fecha_vencimiento, estado='PROGRAMADO', cupo_actual__gt=0).order_by('fecha')
                for ft in future_turnos:
                    if ft.fecha.isoweekday() == int(dia_semana):
                        if suscripcion.clases_restantes <= 0: break
                        existing_reserva = Reserva.objects.filter(turno=ft, usuario=usuario).first()
                        if existing_reserva:
                            if existing_reserva.estado == 'CONFIRMADA': continue
                            existing_reserva.es_recurrente = True
                            existing_reserva.estado = 'CONFIRMADA'
                            existing_reserva.save()
                            ReservaMembresia.objects.get_or_create(reserva=existing_reserva, defaults={'suscripcion': suscripcion})
                        else:
                            res = Reserva.objects.create(turno=ft, usuario=usuario, es_recurrente=True, estado='CONFIRMADA')
                            ReservaMembresia.objects.create(reserva=res, suscripcion=suscripcion)
                        ft.cupo_actual -= 1
                        ft.save()
                        suscripcion.clases_restantes -= 1
                if suscripcion.clases_restantes <= 0:
                    suscripcion.estado = 'AGOTADO'
                suscripcion.save()
        except Exception as e:
            print('Error generating turnos recurrentes admin:', e)
            
        return Response({'id': str(r.id)}, status=201)

    @transaction.atomic
    def delete(self, request, usuario_id, recurrencia_id):
        # Cancel a specific recurrencia for this user
        try:
            recurrencia = Recurrencia.objects.get(id=recurrencia_id, usuario_id=usuario_id, is_active=True)
        except Recurrencia.DoesNotExist:
            return Response({"detail": "Horario fijo no encontrado"}, status=404)
            
        recurrencia.is_active = False
        recurrencia.save()
        
        # Cancel all future confirmed reservations for this recurrencia
        reservas = Reserva.objects.filter(
            usuario_id=usuario_id,
            turno__clase=recurrencia.clase,
            turno__fecha__gte=timezone.localdate(),
            turno__hora_inicio=recurrencia.hora_inicio,
            estado='CONFIRMADA',
            es_recurrente=True
        )
        
        for reserva in reservas:
            reserva.estado = 'CANCELADA_TIEMPO'
            reserva.save()
            turno = reserva.turno
            turno.cupo_actual += 1
            turno.save()
            

            try:
                rm = reserva.consumo_suscripcion
                suscripcion = rm.suscripcion
                rm.delete()
            except Exception:
                suscripcion = None
            if suscripcion:
                suscripcion.clases_restantes += 1
                if suscripcion.estado == 'AGOTADO':
                    suscripcion.estado = 'ACTIVO'
                suscripcion.save()
                
        return Response({"detail": "Horario fijo eliminado exitosamente"})

