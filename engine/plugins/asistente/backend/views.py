from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from .models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA
from .config_loader import get_asistente_config, get_brand_persona

class ConversacionesAdminView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        rol = request.query_params.get('rol', '').strip()

        conversaciones = ConversacionWhatsApp.objects.all().select_related('usuario').prefetch_related('mensajes')

        if q:
            from django.db.models import Q
            conversaciones = conversaciones.filter(
                Q(telefono__icontains=q) |
                Q(usuario__nombre__icontains=q) |
                Q(usuario__apellido__icontains=q) |
                Q(usuario__email__icontains=q)
            )

        if rol and rol != 'TODOS':
            conversaciones = conversaciones.filter(rol_detectado=rol)

        conversaciones = conversaciones.order_by('-updated_at')[:80]

        from core.models import Reserva

        data = []
        for c in conversaciones:
            if c.usuario:
                nombre = f"{c.usuario.nombre} {c.usuario.apellido}".strip()
            else:
                clean_tel = c.telefono.replace('+', '').replace(' ', '').replace('-', '')
                res = Reserva.objects.filter(telefono_temporal__icontains=clean_tel[-8:]).first() if len(clean_tel) >= 8 else None
                if res and res.nombre_temporal:
                    nombre = f"{res.nombre_temporal} (Manual)"
                else:
                    nombre = f"+{c.telefono}" if not c.telefono.startswith('+') else c.telefono

            ultimo_msg = c.mensajes.order_by('-created_at').first()
            data.append({
                'id': str(c.id),
                'telefono': c.telefono,
                'usuario_id': str(c.usuario.id) if c.usuario else None,
                'nombre': nombre,
                'rol_detectado': c.rol_detectado,
                'estado': c.estado,
                'ultimo_mensaje': ultimo_msg.texto if ultimo_msg else "",
                'ultimo_mensaje_at': ultimo_msg.created_at.strftime('%d/%m %H:%M') if ultimo_msg else "",
                'total_mensajes': c.mensajes.count()
            })
        return Response(data)


class ConversacionMensajesAdminView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, conversacion_id):
        try:
            conv = ConversacionWhatsApp.objects.get(id=conversacion_id)
        except ConversacionWhatsApp.DoesNotExist:
            return Response({'detail': 'Conversación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        mensajes = conv.mensajes.all().order_by('created_at')
        return Response([{
            'id': str(m.id),
            'direccion': m.direccion,
            'agente_responsable': m.agente_responsable,
            'texto': m.texto,
            'tools_ejecutadas': m.tools_ejecutadas,
            'created_at': m.created_at.strftime('%d/%m/%Y %H:%M')
        } for m in mensajes])


class TogglePausaHumanoView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, conversacion_id):
        try:
            conv = ConversacionWhatsApp.objects.get(id=conversacion_id)
        except ConversacionWhatsApp.DoesNotExist:
            return Response({'detail': 'Conversación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        if conv.estado == 'ESPERANDO_HUMANO':
            conv.estado = 'ACTIVO'
        else:
            conv.estado = 'ESPERANDO_HUMANO'
        conv.save(update_fields=['estado', 'updated_at'])

        return Response({
            'detail': f'Estado de conversación actualizado a {conv.estado}',
            'estado': conv.estado
        })


class EnviarMensajeManualAdminView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, conversacion_id):
        try:
            conv = ConversacionWhatsApp.objects.get(id=conversacion_id)
        except ConversacionWhatsApp.DoesNotExist:
            return Response({'detail': 'Conversación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        texto = request.data.get('texto', '').strip()
        if not texto:
            return Response({'detail': 'El texto del mensaje no puede estar vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
            client = WhatsAppClient()
            client.send_text_message(conv.telefono, texto)
        except Exception as e:
            return Response({'detail': f'Error al enviar mensaje por WhatsApp: {e}'}, status=status.HTTP_502_BAD_GATEWAY)

        msg = MensajeWhatsAppLog.objects.create(
            conversacion=conv,
            direccion='SALIENTE',
            agente_responsable='humano_admin',
            texto=texto
        )
        conv.save(update_fields=['updated_at'])

        return Response({
            'id': str(msg.id),
            'direccion': msg.direccion,
            'agente_responsable': msg.agente_responsable,
            'texto': msg.texto,
            'tools_ejecutadas': msg.tools_ejecutadas,
            'created_at': msg.created_at.strftime('%d/%m/%Y %H:%M')
        }, status=status.HTTP_201_CREATED)


class AsistenteConfigView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({
            'config': get_asistente_config(),
            'brand_persona': get_brand_persona()
        })
