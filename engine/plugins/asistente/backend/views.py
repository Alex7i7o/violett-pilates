from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA
from .config_loader import get_asistente_config, get_brand_persona

class ConversacionesAdminView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        conversaciones = ConversacionWhatsApp.objects.all().order_by('-updated_at')[:50]
        data = []
        for c in conversaciones:
            nombre = f"{c.usuario.nombre} {c.usuario.apellido}".strip() if c.usuario else "Sin registrar"
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
            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M:%S')
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
        conv.save()

        return Response({
            'detail': f'Estado de conversación actualizado a {conv.estado}',
            'estado': conv.estado
        })


class AsistenteConfigView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({
            'config': get_asistente_config(),
            'brand_persona': get_brand_persona()
        })
