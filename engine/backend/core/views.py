from backend_core.hooks import registry
# Developed by FireSeed - Fueling Innovation
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
import datetime
from django.db import transaction
from .models import Turno, Reserva
from .serializers import TurnoSerializer, BookTurnoSerializer, CancelTurnoSerializer
from .services import cancelar_reserva

class ClientProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        base_data = {
            "name": f"{user.nombre} {user.apellido}",
            "rol": user.rol,
            "activePlan": "Sin plan activo",
            "remainingClasses": 0,
            "totalClasses": 0,
            "expirationDate": "-",
            "daysUntilExpiration": 0,
            "recurrencias": []
        }
        
                # Permitimos que los plugins decoren esta data
        base_data = registry.execute('profile_data', base_data, request=request, user=user)
        
        return Response(base_data)

class TurnosDisponiblesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch upcoming turnos from today onwards, but filter out past times for today
        now = timezone.now()
        today = timezone.localdate(now)
        current_time = now.time()
        
        from django.db.models import Q
        turnos = Turno.objects.select_related('clase').prefetch_related('reservas').filter(
            Q(fecha__gt=today) | Q(fecha=today, hora_inicio__gt=current_time),
            estado='PROGRAMADO'
        ).order_by('fecha', 'hora_inicio')
        serializer = TurnoSerializer(turnos, many=True, context={'request': request})
        return Response(serializer.data)

from rest_framework.throttling import ScopedRateThrottle

class BookTurnoView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'reserva'

    def post(self, request):
        serializer = BookTurnoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        turno_id = serializer.validated_data['turno_id']
        is_recurring = serializer.validated_data['is_recurring']
        
        from .services import process_booking
        success, message = process_booking(
            turno_id=turno_id, 
            user=request.user, 
            is_recurring=is_recurring, 
            request=request
        )
        
        if not success:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"detail": message})


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



# Auth views
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:5173'
    client_class = OAuth2Client

class ClientHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        today = timezone.localdate(now)
        
        req_month = request.query_params.get('month')
        req_year = request.query_params.get('year')
        
        if req_month and req_year:
            target_month = int(req_month)
            target_year = int(req_year)
            start_date = datetime.date(target_year, target_month, 1)
            if target_month == 12:
                end_date = datetime.date(target_year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                end_date = datetime.date(target_year, target_month + 1, 1) - datetime.timedelta(days=1)
            limit_date = min(end_date, today)
        else:
            start_date = today.replace(day=1)
            limit_date = today

        # Clases que el usuario ya tuvo este mes (o hasta la fecha límite)
        # Filtramos por reservas pasadas o de hoy pero con horario finalizado
        current_time = now.time()
        
        reservas = Reserva.objects.select_related('turno', 'turno__clase').filter(
            usuario=user,
            turno__fecha__gte=start_date,
            turno__fecha__lte=limit_date,
            estado__in=['CONFIRMADA', 'TOMADA', 'AUSENTE', 'CANCELADA_TARDIA']
        ).order_by('-turno__fecha', '-turno__hora_inicio')

        # Filter out future classes of today
        historial = []
        for r in reservas:
            if r.turno.fecha < today or (r.turno.fecha == today and r.turno.hora_fin < current_time):
                historial.append({
                    "id": r.id,
                    "turno_id": r.turno.id,
                    "fecha": r.turno.fecha.strftime("%Y-%m-%d"),
                    "hora_inicio": r.turno.hora_inicio.strftime("%H:%M"),
                    "hora_fin": r.turno.hora_fin.strftime("%H:%M"),
                    "clase_nombre": r.turno.clase.nombre,
                    "estado_reserva": r.estado
                })

        return Response(historial)


