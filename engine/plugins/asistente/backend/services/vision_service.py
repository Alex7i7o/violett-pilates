import os
import json
import base64
import logging
from django.utils import timezone
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA, ComprobantePendiente
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

def procesar_comprobante_imagen(phone: str, image_id: str, caption: str = ""):
    """
    Descarga la imagen desde Meta WhatsApp Cloud API y analiza si es un
    comprobante de transferencia bancaria utilizando visión multimodal (gpt-4o-mini).
    Guarda el comprobante en estado PENDIENTE y notifica a la dueña para su aprobación.
    """
    clean_phone = phone.replace('+', '').replace(' ', '')
    conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)

    client = WhatsAppClient()
    image_bytes = client.download_media_bytes(image_id)

    api_key = os.environ.get('OPENAI_API_KEY')
    config = get_asistente_config()
    telefono_duena = config.get('telefono_duena', '').replace('+', '').replace(' ', '')
    
    # 1. Modo Simulación si no hay API key o no se pudo descargar la imagen
    if not api_key or not image_bytes:
        logger.info(f"[ASISTENTE VISION SIMULADOR] Comprobante recibido de {clean_phone} (image_id: {image_id})")
        _atender_comprobante_simulado(conversacion, clean_phone, client, telefono_duena)
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
        banco = datos.get('banco', 'Billetera / Banco')
        
        from plugins.membresias.backend.models import Plan
        plan_coincidente = None
        plan_nom = "Plan personalizado"
        plan_id = ""
        if monto:
            plan_coincidente = Plan.objects.filter(is_active=True, precio=monto).first()
            if plan_coincidente:
                plan_nom = plan_coincidente.nombre
                plan_id = str(plan_coincidente.id)

        usuario = conversacion.usuario
        nombre_alumna = f"{usuario.nombre} {usuario.apellido}".strip() if usuario else (emisor or "Alumna sin registrar")

        # 4. Guardar Comprobante Pendiente de Aprobación
        comp = ComprobantePendiente.objects.create(
            conversacion=conversacion,
            usuario=usuario,
            monto=monto,
            plan_nombre=plan_nom,
            plan_id=plan_id,
            datos_extraidos=datos,
            estado='PENDIENTE'
        )

        # 5. Responder a la alumna informando que administración lo está cotejando
        monto_str = f" por ${monto:,.0f}" if monto else ""
        respuesta_alumna = (
            f"✦ ¡Muchas gracias {nombre_alumna.split()[0]}! Recibimos tu comprobante de transferencia{monto_str} (Op: #{nro_op or comp.id.hex[:6]}).\n\n"
            f"La administración ya fue notificada para cotejar la acreditación en la cuenta. Apenas den el OK, "
            f"se te activarán los créditos y se reservarán tus turnos automáticamente."
        )
        client.send_text_message(clean_phone, respuesta_alumna)
        MensajeWhatsAppLog.objects.create(
            conversacion=conversacion,
            direccion='SALIENTE',
            agente_responsable='agente_finanzas_vision',
            texto=respuesta_alumna
        )

        # 6. Notificar a la dueña por WhatsApp con datos y comando de 1-click
        if telefono_duena:
            comp_short = comp.id.hex[:6]
            msg_duena = (
                f"📥 *NUEVO COMPROBANTE DE PAGO:*\n"
                f"• Alumna: *{nombre_alumna}* ({clean_phone})\n"
                f"• Monto: *${monto:,.0f}* ({plan_nom})\n"
                f"• Banco/App: {banco} | Op: #{nro_op}\n\n"
                f"👉 Para aprobar y acreditarle las clases automáticamente, respondé:\n"
                f"*Aprobar {comp_short}* o *Acreditar a {nombre_alumna.split()[0]}*"
            )
            client.send_text_message(telefono_duena, msg_duena)

    except Exception as e:
        logger.error(f"[ASISTENTE VISION ERROR] {e}", exc_info=True)
        _atender_comprobante_simulado(conversacion, clean_phone, client, telefono_duena)


def _atender_comprobante_simulado(conversacion, clean_phone: str, client: WhatsAppClient, telefono_duena: str):
    usuario = conversacion.usuario
    nombre_alumna = f"{usuario.nombre} {usuario.apellido}".strip() if usuario else "Alumna"
    comp = ComprobantePendiente.objects.create(
        conversacion=conversacion,
        usuario=usuario,
        monto=45000,
        plan_nombre="Plan Mensual - 8 Clases",
        datos_extraidos={"simulado": True},
        estado='PENDIENTE'
    )
    respuesta = (
        f"¡Hola {nombre_alumna}! ✦ Recibimos tu comprobante de pago. La administración ya fue notificada para verificarlo "
        f"en la cuenta y en cuanto den la aprobación te confirmaremos la acreditación de tus clases."
    )
    client.send_text_message(clean_phone, respuesta)
    MensajeWhatsAppLog.objects.create(
        conversacion=conversacion,
        direccion='SALIENTE',
        agente_responsable='agente_finanzas_simulado',
        texto=respuesta
    )
    if telefono_duena:
        comp_short = comp.id.hex[:6]
        msg_duena = (
            f"📥 *NUEVO COMPROBANTE RECIBIDO (Simulado):*\n"
            f"• Alumna: {nombre_alumna} ({clean_phone})\n"
            f"• Monto estimado: $45.000 (Plan Mensual - 8 Clases)\n\n"
            f"👉 Para aprobarlo, respondé:\n*Aprobar {comp_short}* o *Acreditar a {nombre_alumna.split()[0]}*"
        )
        client.send_text_message(telefono_duena, msg_duena)
