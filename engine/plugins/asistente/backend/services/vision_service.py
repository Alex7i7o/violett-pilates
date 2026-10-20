import os
import json
import base64
import logging
from django.utils import timezone
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA

logger = logging.getLogger(__name__)

def procesar_comprobante_imagen(phone: str, image_id: str, caption: str = ""):
    """
    Descarga la imagen desde Meta WhatsApp Cloud API y analiza si es un
    comprobante de transferencia bancaria utilizando visión multimodal (gpt-4o-mini).
    """
    clean_phone = phone.replace('+', '').replace(' ', '')
    conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)

    client = WhatsAppClient()
    image_bytes = client.download_media_bytes(image_id)

    api_key = os.environ.get('OPENAI_API_KEY')
    
    # 1. Modo Simulación si no hay API key o no se pudo descargar la imagen
    if not api_key or not image_bytes:
        logger.info(f"[ASISTENTE VISION SIMULADOR] Comprobante recibido de {clean_phone} (image_id: {image_id})")
        _atender_comprobante_simulado(conversacion, clean_phone, client)
        return

    # 2. Análisis con Vision LLM
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        b64_image = base64.b64encode(image_bytes).decode('utf-8')
        image_data_url = f"data:image/jpeg;base64,{b64_image}"

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=api_key
        )

        prompt_text = """Sos el auditor de cobros de Violett Pilates. Analizá detenidamente esta imagen enviada por WhatsApp y determiná si es un comprobante de transferencia bancaria, pago por Mercado Pago, billetera virtual o depósito bancario.

Respondé ÚNICAMENTE un objeto JSON válido con la siguiente estructura:
{
  "es_comprobante": true/false,
  "monto": 45000.0,
  "fecha": "YYYY-MM-DD",
  "emisor": "Nombre de quien transfirió o null",
  "nro_operacion": "Código de transacción o comprobante",
  "banco": "Banco emisor o app (Mercado Pago, Santander, etc)"
}
Si la imagen no es un comprobante de pago, devolvé {"es_comprobante": false}."""

        msg = HumanMessage(content=[
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": image_data_url}}
        ])

        response = llm.invoke([msg])
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        datos = json.loads(content)

        if not datos.get('es_comprobante', False):
            # No es un comprobante
            respuesta = "¡Hola! ✦ Recibí tu imagen, pero parece no ser un comprobante de transferencia bancaria. Si tenías alguna consulta sobre turnos o planes, contame y con gusto te ayudo."
            client.send_text_message(clean_phone, respuesta)
            MensajeWhatsAppLog.objects.create(
                conversacion=conversacion,
                direccion='SALIENTE',
                agente_responsable='agente_finanzas_vision',
                texto=respuesta
            )
            return

        # 3. Cruzar con planes de la base de datos
        monto = datos.get('monto')
        emisor = datos.get('emisor', '')
        nro_op = datos.get('nro_operacion', '')
        
        from plugins.membresias.backend.models import Plan, Suscripcion
        plan_coincidente = None
        if monto:
            # Buscamos un plan cuyo precio coincida con el monto transferido
            plan_coincidente = Plan.objects.filter(is_active=True, precio=monto).first()

        # Si el usuario está registrado, podemos reactivar o acreditar automáticamente
        usuario = conversacion.usuario
        if usuario and plan_coincidente:
            try:
                from plugins.recurrencias.backend.services import auto_agendar_recurrencias_usuario
                
                # Vencer suscripciones anteriores
                Suscripcion.objects.filter(usuario=usuario, estado__in=['ACTIVO', 'AGOTADO']).update(estado='VENCIDO')

                # Crear nueva suscripción
                today = timezone.localdate()
                nueva_sub = Suscripcion.objects.create(
                    usuario=usuario,
                    plan=plan_coincidente,
                    clases_restantes=plan_coincidente.cantidad_clases,
                    fecha_inicio=today,
                    fecha_vencimiento=today + timezone.timedelta(days=30),
                    estado='ACTIVO'
                )

                # Auto-agendar en sus turnos fijos
                clases_agendadas = auto_agendar_recurrencias_usuario(usuario, nueva_sub)

                # Registrar auditoría
                RegistroAccionIA.objects.create(
                    conversacion=conversacion,
                    tipo_accion='PLAN_REACTIVADO',
                    descripcion=f"Plan {plan_coincidente.nombre} acreditado automáticamente por comprobante de ${monto:,.0f} (Op: {nro_op})",
                    payload=datos
                )

                agendadas_str = f" y ya te agendé automáticamente en tus {clases_agendadas} clases de horarios fijos del mes" if clases_agendadas > 0 else ""
                respuesta = f"✦ ¡Comprobante verificado con éxito! Acreditamos tu {plan_coincidente.nombre} por ${monto:,.0f}{agendadas_str}. Tus créditos ya están listos para usar en Violett Pilates. ¡Nos vemos en el estudio!"
            except Exception as e:
                logger.error(f"Error acreditando plan automáticamente: {e}")
                respuesta = f"✦ ¡Muchas gracias! Recibimos tu comprobante por ${monto:,.0f} (Op: {nro_op}). En breve te confirmaremos la acreditación en tu perfil de Violett."
        else:
            monto_str = f" por ${monto:,.0f}" if monto else ""
            respuesta = f"✦ ¡Muchas gracias! Recibimos tu comprobante de transferencia{monto_str}. Nuestro equipo lo cotejará y te confirmará la acreditación en tu cuenta a la brevedad."

        client.send_text_message(clean_phone, respuesta)
        MensajeWhatsAppLog.objects.create(
            conversacion=conversacion,
            direccion='SALIENTE',
            agente_responsable='agente_finanzas_vision',
            texto=respuesta
        )

    except Exception as e:
        logger.error(f"[ASISTENTE VISION ERROR] {e}", exc_info=True)
        _atender_comprobante_simulado(conversacion, clean_phone, client)


def _atender_comprobante_simulado(conversacion, clean_phone: str, client: WhatsAppClient):
    respuesta = "¡Hola! ✦ Hemos recibido tu comprobante de pago. Lo estamos verificando para acreditar tus créditos en tu cuenta. ¡Muchas gracias por avisarnos!"
    client.send_text_message(clean_phone, respuesta)
    MensajeWhatsAppLog.objects.create(
        conversacion=conversacion,
        direccion='SALIENTE',
        agente_responsable='agente_finanzas_simulado',
        texto=respuesta
    )
