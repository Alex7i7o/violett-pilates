import os
import json
import base64
import logging
from django.utils import timezone
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..models import ConversacionWhatsApp, MensajeWhatsAppLog, RegistroAccionIA, ComprobantePendiente, RegistroErrorIA
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

def obtener_vision_llms_disponibles():
    """
    Retorna una lista de instancias LLM multimodales disponibles ordenadas por robustez:
    1. Google Gemini (gemini-1.5-flash / gemini-2.5-flash / gemini-2.0-flash)
    2. OpenAI (gpt-4o-mini / gpt-4o)
    3. Groq (llama-3.2-11b-vision-preview)
    4. Anthropic (claude-3-5-sonnet-latest)
    """
    llms = []
    gemini_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    groq_key = os.environ.get('GROQ_API_KEY')

    if gemini_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            # gemini-1.5-flash es el modelo multimodal oficial más estable y disponible en todas las cuentas de Google
            candidatos_gemini = [
                os.environ.get('GEMINI_VISION_MODEL', 'gemini-1.5-flash'),
                'gemini-2.0-flash',
                'gemini-1.5-pro'
            ]
            vistos = set()
            for mod in candidatos_gemini:
                if mod and mod not in vistos:
                    vistos.add(mod)
                    try:
                        llms.append(ChatGoogleGenerativeAI(
                            model=mod,
                            google_api_key=gemini_key,
                            temperature=0.0
                        ))
                    except Exception as e_mod:
                        logger.warning(f"[VISION LLM] No se pudo preparar Gemini {mod}: {e_mod}")
        except Exception as eg:
            logger.warning(f"[VISION LLM] Error cargando langchain_google_genai: {eg}")

    if openai_key:
        try:
            from langchain_openai import ChatOpenAI
            llms.append(ChatOpenAI(
                model=os.environ.get('OPENAI_VISION_MODEL', 'gpt-4o-mini'),
                api_key=openai_key,
                temperature=0.0
            ))
        except Exception as eo:
            logger.warning(f"[VISION LLM] Error inicializando ChatOpenAI: {eo}")

    if groq_key:
        try:
            from langchain_groq import ChatGroq
            # qwen/qwen3.8-27b es el modelo multimodal de visión activo oficial en Groq
            groq_vis_model = os.environ.get('GROQ_VISION_MODEL', 'qwen/qwen3.8-27b')
            llms.append(ChatGroq(
                model=groq_vis_model,
                api_key=groq_key,
                temperature=0.0
            ))
        except Exception as egr:
            logger.warning(f"[VISION LLM] Error inicializando ChatGroq Vision: {egr}")

    if anthropic_key:
        try:
            from langchain_anthropic import ChatAnthropic
            llms.append(ChatAnthropic(
                model=os.environ.get('ANTHROPIC_VISION_MODEL', 'claude-3-5-sonnet-latest'),
                api_key=anthropic_key,
                temperature=0.0
            ))
        except Exception as ea:
            logger.warning(f"[VISION LLM] Error inicializando ChatAnthropic: {ea}")

    return llms


def obtener_vision_llm():
    """Retorna la primera instancia LLM multimodal disponible."""
    llms = obtener_vision_llms_disponibles()
    return llms[0] if llms else None


PROMPT_VISION_UNIFICADO = """Sos el auditor inteligente de Violett Pilates. Analizá detenidamente esta imagen enviada por WhatsApp o subida al sistema.

Determiná con precisión qué tipo de documento es:
1. "FICHA_ALUMNA": Planilla física impresa o ficha de papel con encabezado "FICHA ALUMNA" (Violett Gym / Pilates), donde figura el NOMBRE de la alumna arriba y una cuadrícula o tabla con columnas como "N° CLASE" y "FIRMA", con números de clase, fechas manuscritas (ej: 14|10|26), firmas manuscritas o anotaciones ("Vino", "Ausente"), y posibles líneas divisorias horizontales entre abonos.
2. "COMPROBANTE_PAGO": Comprobante bancario, transferencia, Mercado Pago, Santander u otra billetera virtual.
3. "OTRO": Ninguno de los anteriores.

Si es "FICHA_ALUMNA", extraé con máxima rigurosidad:
- nombre_alumna: El nombre de la alumna escrito en el campo "NOMBRE:" (ej: "Luz").
- celular: El celular si figura escrito, o null.
- ciclos: Lista de ciclos/abonos detectados. Si hay una línea divisoria horizontal entre filas (ej: tras la clase 8) o los números de clase se reinician en 1, cada grupo corresponde a un ciclo diferente (ciclo 1 = plan anterior, ciclo 2 = nuevo plan).
  Para cada ciclo extraé la lista de clases en orden:
  - numero_clase: Número de clase del plan (entero, ej: 1, 2, 3...)
  - fecha: Fecha en formato "YYYY-MM-DD" (asumiendo año 2026 para terminación "26", ej: 14/10/26 -> "2026-10-14").
  - fecha_original: Texto tal cual está escrito (ej: "14/10/26" o "14|10|26").
  - estado: "TOMADA" si hay una firma manuscrita, rúbrica o anotación como "Vino". O "AUSENTE" si está en blanco, tachada o dice explícitamente "Ausente".
  - detalle_firma: Breve texto de lo que se observa (ej: "Firmada", "Dice Vino", "Ausente", "Sin firma").

Si es "COMPROBANTE_PAGO", extraé:
- monto: Valor numérico flotante.
- fecha: "YYYY-MM-DD"
- emisor: Nombre de la persona que transfirió.
- nro_operacion: Código de transacción o comprobante.
- banco: Banco emisor o app (Mercado Pago, Santander, etc.).

Respondé ÚNICAMENTE un objeto JSON válido sin bloques markdown ni texto introductorio, con este esquema exacto:
{
  "tipo_documento": "FICHA_ALUMNA" | "COMPROBANTE_PAGO" | "OTRO",
  "ficha": {
    "nombre_alumna": "...",
    "celular": "...",
    "ciclos": [
      {
        "ciclo_numero": 1,
        "clases": [
          {
            "numero_clase": 1,
            "fecha": "2026-10-14",
            "fecha_original": "14/10/26",
            "estado": "TOMADA",
            "detalle_firma": "Firmada"
          }
        ]
      }
    ]
  },
  "comprobante": {
    "es_comprobante": true,
    "monto": 45000.0,
    "fecha": "YYYY-MM-DD",
    "emisor": "...",
    "nro_operacion": "...",
    "banco": "..."
  }
}
"""


def extraer_datos_documento_multimodal(image_bytes: bytes, caption: str = ""):
    """
    Ejecuta el análisis visual multimodal sobre los bytes de una imagen.
    Prueba en cascada los LLMs multimodales disponibles hasta que uno responda con éxito.
    Devuelve (ok: bool, datos: dict, error_msg: str).
    """
    llms = obtener_vision_llms_disponibles()
    if not llms:
        return False, {}, "No hay ningún proveedor de LLM con visión multimodal configurado en el servidor (GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY o ANTHROPIC_API_KEY)."

    try:
        from langchain_core.messages import HumanMessage
        b64_image = base64.b64encode(image_bytes).decode('utf-8')
        image_data_url = f"data:image/jpeg;base64,{b64_image}"

        msg = HumanMessage(content=[
            {"type": "text", "text": PROMPT_VISION_UNIFICADO + (f"\nComentario adicional del usuario: {caption}" if caption else "")},
            {"type": "image_url", "image_url": {"url": image_data_url}}
        ])

        last_err = ""
        for llm in llms:
            try:
                logger.info(f"[VISION LLM] Analizando documento con {llm}...")
                response = llm.invoke([msg])
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]

                datos = json.loads(content.strip())
                return True, datos, ""
            except Exception as e_llm:
                last_err = str(e_llm)
                logger.warning(f"[VISION LLM RETRY] Modelo {llm} falló: {e_llm}")
                continue

        logger.error(f"[VISION EXTRACT ERROR] Fallaron todos los modelos multimodales. Último error: {last_err}")
        return False, {}, last_err
    except Exception as e:
        logger.error(f"[VISION EXTRACT ERROR] Error analizando documento: {e}", exc_info=True)
        return False, {}, str(e)


def procesar_imagen_entrante(phone: str, image_id: str = None, caption: str = "", image_bytes: bytes = None, quoted_wamid: str = None):
    """
    Punto de entrada principal para cualquier imagen recibida por WhatsApp o subida al sistema.
    Descarga la imagen si se pasa image_id y determina si es FICHA_ALUMNA o COMPROBANTE_PAGO.
    Garantiza el registro inmediato tanto de la imagen entrante como de las respuestas en el historial CRM.
    """
    clean_phone = phone.replace('+', '').replace(' ', '')
    conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)
    client = WhatsAppClient()

    # 1. Registrar inmediatamente la foto recibida en el historial del CRM
    caption_txt = f": {caption}" if caption else ""
    MensajeWhatsAppLog.objects.create(
        conversacion=conversacion,
        direccion='ENTRANTE',
        agente_responsable='usuario',
        texto=f"📷 [Foto / Imagen enviada]{caption_txt}"
    )

    if not image_bytes and image_id:
        image_bytes = client.download_media_bytes(image_id)

    config = get_asistente_config()
    telefono_duena = config.get('telefono_duena', '').replace('+', '').replace(' ', '')

    if not image_bytes:
        logger.warning(f"[VISION SERVICE] No se recibieron bytes para la imagen de {clean_phone}")
        resp_fallo = "✦ Recibí la imagen pero hubo un inconveniente al descargarla desde los servidores de WhatsApp. Por favor, volvé a enviarla."
        client.send_text_message(clean_phone, resp_fallo)
        MensajeWhatsAppLog.objects.create(
            conversacion=conversacion,
            direccion='SALIENTE',
            agente_responsable='agente_vision',
            texto=resp_fallo
        )
        return

    ok, datos, err = extraer_datos_documento_multimodal(image_bytes, caption)

    # Si falló la extracción visual
    if not ok:
        logger.error(f"[VISION SERVICE ERROR] {err}")
        # Registrar incidencia en Centinela (RegistroErrorIA)
        try:
            RegistroErrorIA.objects.create(
                tipo_fallo='ERROR_TECNICO_INTERNO',
                mensaje_error=f"Fallo en visión multimodal al procesar imagen: {err}",
                contexto_conversacion={'phone': clean_phone, 'caption': caption, 'image_id': image_id},
                telefono_afectado=clean_phone
            )
        except Exception as e_cent:
            logger.warning(f"[CENTINELA LOG ERROR] {e_cent}")

        _atender_imagen_fallback(conversacion, clean_phone, client, telefono_duena, caption=caption, error_detalle=err)
        return

    tipo_doc = datos.get('tipo_documento', 'OTRO')

    if tipo_doc == 'FICHA_ALUMNA':
        procesar_ficha_alumna_detectada(datos.get('ficha', {}), clean_phone, client, conversacion)
    elif tipo_doc == 'COMPROBANTE_PAGO':
        procesar_comprobante_detectado(datos.get('comprobante', {}), clean_phone, client, conversacion, telefono_duena)
    else:
        # Documento no reconocido
        resp = "¡Hola! ✦ Recibí tu imagen, pero parece no ser una ficha de alumna ni un comprobante de pago. Si tenías alguna consulta sobre horarios o reservas, contame y con gusto te ayudo."
        client.send_text_message(clean_phone, resp)
        MensajeWhatsAppLog.objects.create(
            conversacion=conversacion,
            direccion='SALIENTE',
            agente_responsable='agente_vision',
            texto=resp
        )


def procesar_ficha_alumna_detectada(datos_ficha: dict, clean_phone: str, client: WhatsAppClient, conversacion: ConversacionWhatsApp):
    """
    Procesa los datos extraídos de una FICHA ALUMNA física en papel.
    Arma la propuesta de sincronización, la almacena en los metadatos de la conversación
    y le envía al emisor (Débora o Staff) el resumen detallado para su confirmación ('Confirmar' / 'Sí').
    """
    from ..config_loader import obtener_nombre_staff
    nombre_staff = obtener_nombre_staff(clean_phone)
    if "(" in nombre_staff:
        nombre_staff = nombre_staff.split("(")[0].strip()
    if " " in nombre_staff:
        nombre_staff = nombre_staff.split()[0].strip()
    nombre_staff = nombre_staff or "Deby"

    nombre_raw = datos_ficha.get('nombre_alumna', '').strip()
    from ..tools.gestion_tools import buscar_alumna_flexible
    alumna, matches, err = buscar_alumna_flexible(nombre_raw)

    if not alumna:
        msg = f"✦ {nombre_staff}, leí la ficha física de *'{nombre_raw}'*, pero no encontré ninguna alumna registrada con ese nombre en la base de datos para asociar sus clases.\n\n¿Está anotada con otro nombre o apellido en el sistema?"
        client.send_text_message(clean_phone, msg)
        MensajeWhatsAppLog.objects.create(
            conversacion=conversacion,
            direccion='SALIENTE',
            agente_responsable='agente_vision_fichas',
            texto=msg
        )
        return

    ciclos = datos_ficha.get('ciclos', [])
    total_clases = sum(len(c.get('clases', [])) for c in ciclos)

    if total_clases == 0:
        msg = f"✦ {nombre_staff}, identifiqué la ficha de *{alumna.nombre} {alumna.apellido}*, pero no logré leer ninguna clase o fecha anotada con claridad en la cuadrícula."
        client.send_text_message(clean_phone, msg)
        MensajeWhatsAppLog.objects.create(
            conversacion=conversacion,
            direccion='SALIENTE',
            agente_responsable='agente_vision_fichas',
            texto=msg
        )
        return

    # Guardar la propuesta en los metadatos de la conversación
    conversacion.metadata['propuesta_ficha_alumna'] = {
        'usuario_id': str(alumna.id),
        'usuario_nombre': f"{alumna.nombre} {alumna.apellido}",
        'nombre_leido': nombre_raw,
        'ciclos': ciclos,
        'total_clases': total_clases,
        'created_at': timezone.now().isoformat()
    }
    conversacion.save(update_fields=['metadata'])

    # Construir mensaje de previsualización para confirmación
    lineas = [
        f"✦ **¡Hola {nombre_staff}! Leí la ficha física de {alumna.nombre} {alumna.apellido}:**\n",
        f"📋 Encontré **{total_clases} clases** registradas en el papel:\n"
    ]

    for c in ciclos:
        c_num = c.get('ciclo_numero', 1)
        clases_c = c.get('clases', [])
        if len(ciclos) > 1:
            tit = "📌 **Plan Anterior (Finalizado):**" if c_num == 1 else "📌 **Nuevo Plan (Ciclo Actual):**"
            lineas.append(tit)
        for cl in clases_c:
            num = cl.get('numero_clase')
            f_orig = cl.get('fecha_original') or cl.get('fecha')
            st = "✓ Asistió" if cl.get('estado') == 'TOMADA' else "✕ Ausente"
            det = cl.get('detalle_firma', 'Firmada')
            lineas.append(f"• Clase {num}: {f_orig} — {st} ({det})")
        lineas.append("")

    lineas.append("💡 **¿Querés que guarde estos cambios y actualice sus créditos?**")
    lineas.append("👉 Respondé **'Confirmar'** o **'Sí'** para sincronizar su historial en la base de datos, o indicame si querés corregir alguna fecha.")

    texto_final = "\n".join(lineas)
    client.send_text_message(clean_phone, texto_final)

    MensajeWhatsAppLog.objects.create(
        conversacion=conversacion,
        direccion='SALIENTE',
        agente_responsable='agente_vision_fichas',
        texto=texto_final
    )


def procesar_comprobante_detectado(datos_comp: dict, clean_phone: str, client: WhatsAppClient, conversacion: ConversacionWhatsApp, telefono_duena: str):
    """
    Procesa un comprobante bancario verificado por la IA de visión.
    """
    monto = datos_comp.get('monto')
    emisor = datos_comp.get('emisor', '')
    nro_op = datos_comp.get('nro_operacion', '')
    banco = datos_comp.get('banco', 'Billetera / Banco')

    from plugins.membresias.backend.models import Plan
    plan_nom = "Plan personalizado"
    plan_id = ""
    if monto:
        plan_coincidente = Plan.objects.filter(is_active=True, precio=monto).first()
        if plan_coincidente:
            plan_nom = plan_coincidente.nombre
            plan_id = str(plan_coincidente.id)

    usuario = conversacion.usuario
    nombre_alumna = f"{usuario.nombre} {usuario.apellido}".strip() if usuario else (emisor or "Alumna sin registrar")

    comp = ComprobantePendiente.objects.create(
        conversacion=conversacion,
        usuario=usuario,
        monto=monto,
        plan_nombre=plan_nom,
        plan_id=plan_id,
        datos_extraidos=datos_comp,
        estado='PENDIENTE'
    )

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


def _atender_imagen_fallback(conversacion, clean_phone: str, client: WhatsAppClient, telefono_duena: str, caption: str = "", error_detalle: str = ""):
    """Fallback si ocurre un inconveniente técnico al procesar la imagen."""
    usuario = conversacion.usuario
    nombre_alumna = f"{usuario.nombre} {usuario.apellido}".strip() if usuario else "Alumna"

    # Si el remitente es la dueña o staff autorizado, orientarla con mensaje prolijo
    from ..config_loader import es_telefono_staff_o_duena
    if es_telefono_staff_o_duena(clean_phone) or getattr(conversacion, 'rol_detectado', '') == 'DUENA':
        msg = (
            "✦ Deby, recibí la foto de la ficha pero en este momento no pude leer los datos automáticamente.\n\n"
            "📸 **Opciones para continuar:**\n"
            "1. Podés reenviármela asegurando buena iluminación y enfoque nítido sobre la cuadrícula.\n"
            "2. O podés escanearla o cargarla directamente desde el sistema web en: *Alumnas ➔ Seleccionar Alumna ➔ Clases / Asistencia ➔ 'Escanear Ficha Física'*, donde podés revisar y confirmar cada clase al instante."
        )
        client.send_text_message(clean_phone, msg)
        MensajeWhatsAppLog.objects.create(
            conversacion=conversacion,
            direccion='SALIENTE',
            agente_responsable='agente_vision',
            texto=msg
        )
        return

    # Si es una alumna
    comp = ComprobantePendiente.objects.create(
        conversacion=conversacion,
        usuario=usuario,
        monto=45000,
        plan_nombre="Plan Mensual - 8 Clases",
        datos_extraidos={"simulado": True, "caption": caption, "error": error_detalle},
        estado='PENDIENTE'
    )
    respuesta = (
        f"¡Hola {nombre_alumna}! ✦ Recibimos tu imagen. La administración ya fue notificada para verificarla y acompañarte."
    )
    client.send_text_message(clean_phone, respuesta)
    MensajeWhatsAppLog.objects.create(
        conversacion=conversacion,
        direccion='SALIENTE',
        agente_responsable='agente_finanzas_simulado',
        texto=respuesta
    )


# Alias para retrocompatibilidad
def procesar_comprobante_imagen(phone: str, image_id: str, caption: str = "", quoted_wamid: str = None):
    return procesar_imagen_entrante(phone=phone, image_id=image_id, caption=caption, quoted_wamid=quoted_wamid)
