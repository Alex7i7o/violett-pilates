import hmac
import hashlib
import base64
import json
import uuid
import logging
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import SolicitudEliminacionDatos

logger = logging.getLogger(__name__)

def parse_signed_request(signed_request, secret):
    """
    Decodifica el signed_request enviado por Meta cuando un usuario elimina la aplicación.
    """
    try:
        encoded_sig, payload = signed_request.split('.', 1)
        # Fix base64 padding
        sig = base64.urlsafe_b64decode(encoded_sig + '=' * (-len(encoded_sig) % 4))
        data = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)).decode('utf-8'))
        
        # Opcional: verificar firma si tenemos secret configurado
        if secret:
            expected_sig = hmac.new(secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).digest()
            if not hmac.compare_digest(sig, expected_sig):
                logger.warning("[DATA DELETION] Firma inválida de Meta signed_request.")
        return data
    except Exception as e:
        logger.warning(f"[DATA DELETION] Error decodificando signed_request: {e}")
        return None


class DataDeletionCallbackView(APIView):
    """
    Endpoint de devolución de llamada de eliminación de datos de Meta (Data Deletion Callback URL).
    Cumple con el protocolo oficial de Meta Platform para Facebook Login y WhatsApp API.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code') or request.GET.get('id')
        if code:
            sol = SolicitudEliminacionDatos.objects.filter(codigo_confirmacion=code).first()
            if sol:
                return Response({
                    "codigo_confirmacion": sol.codigo_confirmacion,
                    "estado": sol.estado,
                    "fecha_solicitud": sol.created_at.isoformat(),
                    "mensaje": f"Tu solicitud de eliminación se encuentra en estado: {sol.get_estado_display()}."
                }, status=status.HTTP_200_OK)
            return Response({"error": "Código de seguimiento no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "servicio": "Violett Pilates - Gestión de Eliminación de Datos",
            "instrucciones_url": "https://violett.com.ar/eliminar-datos",
            "legislacion": "Ley 25.326 de Protección de Datos Personales (Argentina) y Políticas de Meta"
        }, status=status.HTTP_200_OK)

    def post(self, request):
        signed_request = request.data.get('signed_request') or request.POST.get('signed_request')
        user_id = None

        if signed_request:
            secret = getattr(settings, 'FACEBOOK_APP_SECRET', None) or getattr(settings, 'META_APP_SECRET', None)
            parsed_data = parse_signed_request(signed_request, secret)
            if parsed_data:
                user_id = parsed_data.get('user_id')

        # Generar código único de confirmación exigido por Meta
        confirm_code = f"del_{uuid.uuid4().hex[:12]}"

        solicitud = SolicitudEliminacionDatos.objects.create(
            codigo_confirmacion=confirm_code,
            user_id_meta=str(user_id) if user_id else None,
            motivo="Solicitud automática de revocación de permisos desde Meta",
            estado='PENDIENTE'
        )

        logger.info(f"[DATA DELETION] Solicitud registrada desde Meta: {confirm_code} (User ID Meta: {user_id})")

        # URL de estado requerida por Meta
        status_url = f"https://violett.com.ar/eliminar-datos?code={confirm_code}"

        return JsonResponse({
            "url": status_url,
            "confirmation_code": confirm_code
        })


class SolicitarEliminacionWebAPIView(APIView):
    """
    Endpoint público para que los usuarios envíen solicitudes de eliminación de datos
    directamente desde el formulario de la página web /eliminar-datos.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        telefono = request.data.get('telefono', '').strip()
        motivo = request.data.get('motivo', '').strip()

        if not email and not telefono:
            return Response(
                {"error": "Por favor ingresá al menos tu correo electrónico o tu número de teléfono registrado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        confirm_code = f"DEL-{uuid.uuid4().hex[:8].upper()}"

        SolicitudEliminacionDatos.objects.create(
            codigo_confirmacion=confirm_code,
            email=email if email else None,
            telefono=telefono if telefono else None,
            motivo=motivo if motivo else "Solicitud manual enviada desde formulario web",
            estado='PENDIENTE'
        )

        logger.info(f"[DATA DELETION] Solicitud manual web registrada: #{confirm_code} ({email or telefono})")

        return Response({
            "success": True,
            "codigo_confirmacion": confirm_code,
            "mensaje": f"Tu solicitud #{confirm_code} fue recibida correctamente. Procesaremos la eliminación definitiva de tus datos en un plazo máximo de 48 horas hábiles conforme a la Ley 25.326."
        }, status=status.HTTP_201_CREATED)
