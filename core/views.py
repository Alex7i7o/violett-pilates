# Developed by FireSeed - Fueling Innovation
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from .models import Turno, Reserva, Suscripcion, Recurrencia
from .serializers import TurnoSerializer, BookTurnoSerializer, CancelTurnoSerializer, RecurrenciaSerializer
from .services import cancelar_reserva

class ClientProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        suscripcion = Suscripcion.objects.filter(usuario=user, estado='ACTIVO').first()
        
        if not suscripcion:
            return Response({
                "name": f"{user.nombre} {user.apellido}",
                "activePlan": "Sin plan activo",
                "remainingClasses": 0,
                "totalClasses": 0,
                "expirationDate": "-",
                "daysUntilExpiration": 0,
                "recurrencias": []
            })
            
        dias_restantes = (suscripcion.fecha_vencimiento - timezone.now().date()).days
        
        recurrencias = Recurrencia.objects.filter(usuario=user, is_active=True)
        recurrencias_data = RecurrenciaSerializer(recurrencias, many=True).data
        
        return Response({
            "name": f"{user.nombre} {user.apellido}",
            "activePlan": suscripcion.plan.nombre,
            "remainingClasses": suscripcion.clases_restantes,
            "totalClasses": suscripcion.plan.cantidad_clases,
            "expirationDate": suscripcion.fecha_vencimiento.strftime("%Y-%m-%d"),
            "daysUntilExpiration": max(0, dias_restantes),
            "recurrencias": recurrencias_data
        })

class TurnosDisponiblesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch upcoming turnos from today onwards, but filter out past times for today
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        from django.db.models import Q
        turnos = Turno.objects.filter(
            Q(fecha__gt=today) | Q(fecha=today, hora_inicio__gt=current_time),
            estado='PROGRAMADO'
        ).order_by('fecha', 'hora_inicio')
        serializer = TurnoSerializer(turnos, many=True, context={'request': request})
        return Response(serializer.data)

class BookTurnoView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = BookTurnoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        turno_id = serializer.validated_data['turno_id']
        is_recurring = serializer.validated_data['is_recurring']
        user = request.user
        
        try:
            turno = Turno.objects.select_for_update().get(id=turno_id, estado='PROGRAMADO')
        except Turno.DoesNotExist:
            return Response({"detail": "Turno no encontrado o no disponible."}, status=status.HTTP_404_NOT_FOUND)
            
        # Check if already booked
        reserva = Reserva.objects.filter(turno=turno, usuario=user).first()
        if reserva and reserva.estado == 'CONFIRMADA':
            return Response({"detail": "Ya tienes una reserva para este turno."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check spots
        if turno.cupo_actual <= 0:
            return Response({"detail": "El turno está lleno."}, status=status.HTTP_400_BAD_REQUEST)
            

        # Check active subscription and remaining classes
        suscripcion = Suscripcion.objects.filter(usuario=user, estado='ACTIVO', clases_restantes__gt=0).first()
        if not suscripcion:
            return Response({"detail": "No tienes un plan activo o clases restantes."}, status=status.HTTP_400_BAD_REQUEST)
            
        if is_recurring:
            weekday = turno.fecha.isoweekday()
            active_recs = Recurrencia.objects.filter(
                clase=turno.clase,
                dia_semana=weekday,
                hora_inicio=turno.hora_inicio,
                is_active=True
            ).count()
            if active_recs >= turno.clase.cupo_maximo:
                return Response({"detail": "No hay cupos fijos disponibles, solo puntuales."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Create or update reservation logic
        if is_recurring:
            weekday = turno.fecha.isoweekday()
            
            # Save rule
            Recurrencia.objects.get_or_create(
                usuario=user,
                clase=turno.clase,
                dia_semana=weekday,
                hora_inicio=turno.hora_inicio,
                defaults={'is_active': True}
            )

            # Find all available future turnos matching the criteria
            future_turnos = Turno.objects.filter(
                clase=turno.clase,
                hora_inicio=turno.hora_inicio,
                fecha__gte=turno.fecha,
                fecha__lte=suscripcion.fecha_vencimiento,
                estado='PROGRAMADO',
                cupo_actual__gt=0
            ).order_by('fecha')

            # Filter by weekday in memory (sqlite doesn't have good isoweekday query support)
            future_turnos_list = [t for t in future_turnos if t.fecha.isoweekday() == weekday]
            
            if len(future_turnos_list) <= 1:
                return Response({"detail": "Esta es una clase única o tu plan vence antes de la próxima sesión. No se puede establecer como horario fijo."}, status=status.HTTP_400_BAD_REQUEST)
            
            reservas_creadas = 0
            for ft in future_turnos_list:
                if suscripcion.clases_restantes <= 0:
                    break
                    
                # Check if already booked
                existing_reserva = Reserva.objects.filter(turno=ft, usuario=user).first()
                if existing_reserva:
                    if existing_reserva.estado == 'CONFIRMADA':
                        continue
                    existing_reserva.suscripcion = suscripcion
                    existing_reserva.es_recurrente = True
                    existing_reserva.estado = 'CONFIRMADA'
                    existing_reserva.save()
                else:
                    Reserva.objects.create(
                        turno=ft,
                        usuario=user,
                        suscripcion=suscripcion,
                        es_recurrente=True,
                        estado='CONFIRMADA'
                    )
                
                ft.cupo_actual -= 1
                ft.save()
                
                suscripcion.clases_restantes -= 1
                reservas_creadas += 1

            if suscripcion.clases_restantes == 0:
                suscripcion.estado = 'AGOTADO'
            suscripcion.save()

            if reservas_creadas == 0:
                return Response({"detail": "No se pudieron agendar turnos recurrentes (falta de cupo o plan agotado)."}, status=status.HTTP_400_BAD_REQUEST)
                
        else:
            if reserva:
                reserva.suscripcion = suscripcion
                reserva.es_recurrente = False
                reserva.estado = 'CONFIRMADA'
                reserva.save()
            else:
                Reserva.objects.create(
                    turno=turno,
                    usuario=user,
                    suscripcion=suscripcion,
                    es_recurrente=False,
                    estado='CONFIRMADA'
                )
            
            turno.cupo_actual -= 1
            turno.save()
            
            suscripcion.clases_restantes -= 1
            if suscripcion.clases_restantes == 0:
                suscripcion.estado = 'AGOTADO'
            suscripcion.save()
        
        return Response({"detail": "Reserva confirmada exitosamente."})

class CancelTurnoView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CancelTurnoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        turno_id = serializer.validated_data['turno_id']
        user = request.user
        
        exito, mensaje = cancelar_reserva(turno_id, user)
        if not exito:
            return Response({"detail": mensaje}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({"detail": mensaje})

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
            turno__fecha__gte=timezone.now().date(),
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
            
            suscripcion = reserva.suscripcion
            suscripcion.clases_restantes += 1
            if suscripcion.estado == 'AGOTADO':
                suscripcion.estado = 'ACTIVO'
            suscripcion.save()
            
        return Response({"detail": "Horario fijo cancelado exitosamente."})

# Auth views
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:5173'
    client_class = OAuth2Client
