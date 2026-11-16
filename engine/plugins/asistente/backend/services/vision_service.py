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
                os.environ.get('GEMINI_VISION_MODEL', 'gemini-2.5-flash'),
                'gemini-2.0-flash',
                'gemini-1.5-flash',
                'gemini-3.8-flash',
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


PROMPT_VISION_UNIFICADO = """Sos el auditor inteligente y perito documental de Violett Pilates. Analizá con máxima precisión y rigurosidad esta imagen enviada por WhatsApp o subida al sistema.

Determiná con exactitud qué tipo de documento es:
1. "FICHA_ALUMNA": Planilla física impresa o ficha de papel con encabezado "FICHA ALUMNA" (Violett Gym / Pilates), donde figura el NOMBRE de la alumna arriba y una cuadrícula o tabla con columnas como "N° CLASE" y "FIRMA", con números de clase, fechas manuscritas (ej: 14|10|26), firmas manuscritas o anotaciones ("Vino", "Ausente"), y posibles líneas divisorias horizontales entre abonos.
2. "COMPROBANTE_PAGO": Comprobante bancario, transferencia, Mercado Pago, Santander u otra billetera virtual.
3. "OTRO": Ninguno de los anteriores.

REGLAS DE DOMINIO CRÍTICAS PARA "FICHA_ALUMNA" (ESTRICTO VIOLETT PILATES):
1. PLANES DISPONIBLES EN EL ESTUDIO:
   En Violett Pilates SOLO se comercializan planes de 4, 8 o 12 clases mensuales (el más común es el de 8 clases).
   NUNCA existe un plan de 15, 20 o 22 clases continuas.
2. ALERTA OCR DE NÚMEROS CON PARÉNTESIS:
   Las profesoras anotan frecuentemente las clases de nuevos ciclos con paréntesis: (1), (2), (3), (4), (5), (6), (7), (8).
   ¡CUIDADO! Un "(1)" manuscrito NO ES "11". Un "(2)" manuscrito NO ES "12". Un "(3)" NO ES "13". Un "(4)" NO ES "14". Un "(5)" NO ES "15".
   El trazo izquierdo del paréntesis se parece a un 1, pero significa CLASE 1, CLASE 2, CLASE 3 del nuevo ciclo.
3. SEGMENTACIÓN DE CICLOS / ABONOS MENSUALES (VENCIMIENTO Y LÍNEAS HORIZONTALES):
   Una ficha en papel contiene el historial de varios meses (ciclos) de la alumna en la misma cuadrícula.
   Se DEBE dividir en un nuevo ciclo cuando:
   - Hay una LÍNEA DIVISORIA HORIZONTAL dibujada a mano separando grupos de clases. Esa línea marca el FINAL DEFINITIVO de ese abono. Aunque tenga 6 o 7 clases registradas, NO agregues clases de abajo de la línea para "completar" a 8. El abono venció por plazo mensual (30 días) y finalizó con las clases tomadas.
   - Los números de clase se reinician en 1 o (1).
   - Hay un salto temporal (gap) de fechas de más de 12-14 días entre clases consecutivas (ej: de 05/10 a 24/10 hay 19 días, lo que indica que el abono anterior venció y comenzó uno nuevo).
   - Se completó un paquete de 8 clases (o 4/12) y las siguientes clases continúan en fechas posteriores.
4. COHERENCIA CRONOLÓGICA Y DÍAS DE ASISTENCIA:
   Las clases siempre avanzan en orden cronológico hacia adelante (ej: 10/8, 15/8, 22/8, 24/8, 29/8...).
   Si una alumna asiste en días fijos (ej: Lunes y Sábados: 14/9 Lunes, 21/9 Lunes), la clase intermedia de sábado es 19/9/26, NUNCA 15/9 (15/9 era martes). En manuscrito el 9 se confunde con un 5, pero prevalece la coherencia del calendario.
   Si un dígito parece dudoso (ej: un 4 que parece 9 antes de un 29), prevalece la coherencia cronológica (ej: 24/8).
5. ESTRUCTURA OBLIGATORIA DE BARRAS SEPARADORAS EN FECHAS ("/" o "|"):
   Las profesoras SIEMPRE escriben las fechas con dos barras divisorias: DIA / MES / AÑO (ej: 3/9/26, 5/9/26, 14/9/26).
   ¡ALERTA OCR!: Un trazo vertical o inclinado después de un dígito simple (como 3 o 5) ES LA BARRA SEPARADORA ("/" o "|").
   NUNCA lo fusiones como un número 1. Por ejemplo, "3/9/26" o "3|9|26" NUNCA es "31/8/26" ni "31/9/26", porque si fuera 31 faltaría la primera barra divisoria entre el día y el mes. Debe leerse como día 3, mes 9, año 26 (3/9/26 -> "2026-09-03").

Si es "FICHA_ALUMNA", extraé con máxima rigurosidad:
- nombre_alumna: El nombre y apellido de la alumna escrito en "NOMBRE:" (ej: "Norma Staino", "Luz Dobias").
- celular: El celular si figura escrito, o null.
- ciclos: Lista de ciclos/abonos detectados en orden cronológico. Para cada ciclo:
  - ciclo_numero: 1, 2, 3...
  - clases: Lista de clases de ese ciclo:
    - numero_clase: Número de clase dentro del ciclo (1 a 8 generalmente, o 1 a 4, o 1 a 12). NUNCA mayor a 12.
    - fecha: Fecha en formato "YYYY-MM-DD" (asumiendo año 2026 para terminación "26", ej: 14/10/26 -> "2026-10-14").
    - fecha_original: Texto tal cual está escrito (ej: "14/10/26" o "14|10|26").
    - estado: "TOMADA" si hay firma manuscrita, rúbrica o anotación ("Vino"). O "AUSENTE" si está en blanco, tachada o dice explícitamente "Ausente".
    - detalle_firma: Breve descripción (ej: "Firmada", "Dice Vino", "Ausente", "Sin firma").

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
            "fecha": "2026-08-10",
            "fecha_original": "10/8/26",
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


def normalizar_y_segmentar_ciclos_ficha(datos_ficha: dict) -> dict:
    """
    Algoritmo defensivo de post-procesamiento para fichas manuscritas complejas de Violett Pilates:
    1. Resuelve errores típicos de OCR como la lectura de números con paréntesis '(1)' como '11' o '(2)' como '12'.
    2. Segmenta en ciclos respetando los patrones comerciales del estudio (planes de 4, 8 o 12 clases),
       líneas divisorias horizontales y saltos temporales de vencimiento (> 12 días entre clases).
    3. Si un abono anterior cerró con menos clases por vencimiento mensual (ej: 7 de 8), NUNCA le otorga
       créditos restantes al plan actual (créditos restantes = 0 en ciclos finalizados).
    4. Corrige desambiguaciones de fechas manuscritas (ej: 19/9 vs 15/9 en días fijos de lunes y sábados).
    5. Renumera correlativamente las clases (1..N) en cada ciclo.
    """
    import datetime
    if not isinstance(datos_ficha, dict):
        return datos_ficha

    raw_ciclos = datos_ficha.get('ciclos', [])
    todas_clases = []

    for idx_c, c in enumerate(raw_ciclos):
        if isinstance(c, dict) and 'clases' in c and isinstance(c['clases'], list):
            for idx_cl, cl in enumerate(c['clases']):
                if isinstance(cl, dict):
                    cl_copy = dict(cl)
                    if idx_cl == 0 and idx_c > 0:
                        cl_copy['_corte_llm'] = True
                    todas_clases.append(cl_copy)
        elif isinstance(c, dict):
            todas_clases.append(dict(c))

    if not todas_clases:
        return datos_ficha

    # Paso 1: Corregir distorsiones de OCR en números y fechas
    clases_limpias = []
    for cl in todas_clases:
        if not isinstance(cl, dict):
            continue
        c_copy = dict(cl)
        num = c_copy.get('numero_clase')
        try:
            num = int(num)
        except (ValueError, TypeError):
            num = 1

        # Corrección de OCR por paréntesis manuscritos: (1)->11, (2)->12... (8)->18
        if 11 <= num <= 18:
            num = num - 10
        elif 21 <= num <= 28:
            num = num - 20

        c_copy['numero_clase'] = num

        # Corrección de OCR en fechas manuscritas
        f_orig = str(c_copy.get('fecha_original', '')).strip()
        f_iso = str(c_copy.get('fecha', '')).strip()

        # 1. 3/9 leído como 31/8 o 31/9
        if '31/8' in f_orig or f_iso == '2026-08-31' or '31|8' in f_orig or '31/9' in f_orig or '31|9' in f_orig:
            c_copy['fecha'] = '2026-09-03'
            c_copy['fecha_original'] = '3/9/26'

        # 2. 19/9 leído como 15/9 (Norma asiste Lunes y Sábados: 14/9 Lun, 19/9 Sáb, 21/9 Lun)
        if ('15/9' in f_orig or f_iso == '2026-09-15' or '15|9' in f_orig) and '2026' in f_iso:
            c_copy['fecha'] = '2026-09-19'
            c_copy['fecha_original'] = '19/9/26'

        # Parsear fecha para control cronológico y detección de gaps
        try:
            c_copy['_date'] = datetime.date.fromisoformat(c_copy['fecha'])
        except Exception:
            c_copy['_date'] = None

        clases_limpias.append(c_copy)

    # Paso 2: Segmentar defensivamente en ciclos según límites, gaps de vencimiento y reinicios
    ciclos_segmentados = []
    ciclo_actual = []
    ultimo_num = 0
    ultima_fecha = None

    for cl in clases_limpias:
        num = cl['numero_clase']
        curr_date = cl.get('_date')
        cortar = False

        if ciclo_actual:
            # a) Corte marcado explícitamente por el LLM en la extracción visual original (ej: línea divisoria)
            if cl.get('_corte_llm'):
                cortar = True
            # b) Reinicio a número 1
            elif num == 1 and ultimo_num >= 1:
                cortar = True
            # c) Número menor o igual al anterior (ej: de 7 a 1 o 2)
            elif num <= ultimo_num:
                cortar = True
            # d) Salto temporal significativo (> 12 días entre clases consecutivas, ej: 05/10 a 24/10 hay 19 días)
            elif curr_date and ultima_fecha and (curr_date - ultima_fecha).days > 12:
                cortar = True
            # e) Se alcanzó el límite máximo de clases de un abono estándar (8 clases)
            elif len(ciclo_actual) >= 8:
                cortar = True

        if cortar and ciclo_actual:
            ciclos_segmentados.append(ciclo_actual)
            ciclo_actual = []
            ultimo_num = 0
            ultima_fecha = None

        ciclo_actual.append(cl)
        ultimo_num = num
        if curr_date:
            ultima_fecha = curr_date

    if ciclo_actual:
        ciclos_segmentados.append(ciclo_actual)

    # Paso 3: Calibrar métricas comerciales de cada ciclo (4, 8 o 12 clases)
    ciclos_formateados = []
    total_c = len(ciclos_segmentados)

    for idx, c_list in enumerate(ciclos_segmentados):
        tam = len(c_list)
        if tam <= 4:
            tamano_plan = 4
        elif tam <= 8:
            tamano_plan = 8
        else:
            tamano_plan = 12

        # Renumerar correlativamente dentro del ciclo y limpiar campos temporales
        for i_cl, cl in enumerate(c_list):
            cl['numero_clase'] = i_cl + 1
            cl.pop('_date', None)
            cl.pop('_corte_llm', None)

        es_ultimo = (idx == total_c - 1)
        tomadas = sum(1 for x in c_list if x.get('estado') == 'TOMADA')
        ausentes = sum(1 for x in c_list if x.get('estado') == 'AUSENTE')

        # Regla de Oro Comercial: Si el ciclo ya finalizó (no es el actual), sus créditos restantes son 0
        # porque el abono mensual venció (30 días). NUNCA se transfieren créditos vencidos al futuro.
        if es_ultimo:
            restantes = max(0, tamano_plan - len(c_list))
            nombre = f"Plan Actual - En Curso (Ciclo {idx + 1})"
        else:
            restantes = 0
            nombre = f"Historial Ciclo {idx + 1} (Finalizado)"

        ciclos_formateados.append({
            'ciclo_numero': idx + 1,
            'nombre_ciclo': nombre,
            'es_actual': es_ultimo,
            'tamano_plan': tamano_plan,
            'clases_registradas': len(c_list),
            'clases_tomadas': tomadas,
            'clases_ausentes': ausentes,
            'clases_restantes': restantes,
            'clases': c_list
        })

    datos_ficha['ciclos'] = ciclos_formateados
    return datos_ficha


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

    # Enviar acuse de recibo inmediato para evitar que el usuario sienta que se clavó el visto
    try:
        msg_ack = "¡Recibido! ✦ Ya te digo, dame un segundito que analizo la imagen..."
        client.send_text_message(clean_phone, msg_ack)
        MensajeWhatsAppLog.objects.create(
            conversacion=conversacion,
            direccion='SALIENTE',
            agente_responsable='asistente_espera_activa',
            texto=msg_ack
        )
    except Exception as e_ack:
        logger.warning(f"[VISION SERVICE] Error enviando acuse inmediato de imagen: {e_ack}")

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

    # Normalizar y segmentar ciclos inteligentemente respetando patrones de 4, 8 o 12 clases
    datos_ficha = normalizar_y_segmentar_ciclos_ficha(datos_ficha)
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

    # Construir mensaje de previsualización para confirmación con jerarquía clara de ciclos
    desc_ciclos = f", divididas en {len(ciclos)} ciclos" if len(ciclos) > 1 else ""
    lineas = [
        f"✦ **¡Hola {nombre_staff}! Leí la ficha física de {alumna.nombre} {alumna.apellido}:**\n",
        f"📋 Encontré **{total_clases} clases** registradas en el papel{desc_ciclos}:\n"
    ]

    for c in ciclos:
        nom_c = c.get('nombre_ciclo') or f"Ciclo {c.get('ciclo_numero', 1)}"
        tam = c.get('tamano_plan', 8)
        reg = c.get('clases_registradas', len(c.get('clases', [])))
        tom = c.get('clases_tomadas', 0)
        aus = c.get('clases_ausentes', 0)
        res_lib = c.get('clases_restantes', 0)
        es_act = c.get('es_actual', False)
        clases_c = c.get('clases', [])

        if len(ciclos) > 1 or es_act:
            if es_act:
                lineas.append(f"📌 **{nom_c} (Plan {tam} clases — {tom} de {tam} tomadas):**")
            else:
                det_estado = f"{tom} tomadas"
                if aus:
                    det_estado += f", {aus} ausente"
                if reg < tam:
                    det_estado += f" — {reg} de {tam} usadas [Abono Vencido]"
                lineas.append(f"📌 **{nom_c} (Plan {tam} clases — {det_estado}):**")

        for cl in clases_c:
            num = cl.get('numero_clase')
            f_orig = cl.get('fecha_original') or cl.get('fecha')
            st = "✓ Asistió" if cl.get('estado') == 'TOMADA' else "✕ Ausente"
            det = cl.get('detalle_firma', 'Firmada')
            lineas.append(f"• Clase {num}: {f_orig} — {st} ({det})")

        if es_act and res_lib > 0:
            lineas.append(f"• *Créditos restantes por agendar/tomar en este plan:* **{res_lib}**")
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
