import logging
import threading
from django.utils import timezone
from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

# Buffer en memoria para Message Debouncing (agrupación de ráfagas de mensajes de WhatsApp)
DEBOUNCE_BUFFERS = {}  # clean_phone -> {'texts': [...], 'timer': Timer, 'data': dict}
DEBOUNCE_LOCK = threading.Lock()
DEBOUNCE_WINDOW_SECONDS = 2.5

def _flush_debounced_message(clean_phone: str):
    with DEBOUNCE_LOCK:
        entry = DEBOUNCE_BUFFERS.pop(clean_phone, None)

    if not entry:
        return

    texts = [t for t in entry.get('texts', []) if t and t.strip()]
    if not texts:
        return

    merged_text = "\n".join(texts)
    data = dict(entry.get('data', {}))
    data['text'] = merged_text

    if len(texts) > 1:
        logger.info(f"[MESSAGE DEBOUNCER] Agrupados {len(texts)} mensajes de {clean_phone} en una sola interacción.")
        print(f"[MESSAGE DEBOUNCER] Agrupados {len(texts)} mensajes de {clean_phone} en una sola llamada:\n'{merged_text}'", flush=True)

    thread = threading.Thread(target=_ejecutar_ciclo_agente, args=(data,), daemon=True)
    thread.start()

def procesar_mensaje_entrante_async(data: dict):
    """
    Despacha el procesamiento del mensaje en un thread secundario.
    Aplica Message Debouncing (ventana de 2.5s) para mensajes de texto consecutivos,
    evitando disparar múltiples flujos paralelos y respuestas superpuestas cuando el usuario escribe en ráfagas.
    Los mensajes de audio o interactivos (botones) se procesan de inmediato.
    """
    phone = data.get('phone', '')
    clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
    es_audio = data.get('es_audio', False)
    raw_m = data.get('raw_msg', {})
    msg_type = raw_m.get('type') if isinstance(raw_m, dict) else ''

    # Audio, imagen o botón interactivo: procesar inmediatamente sin buffer
    if es_audio or msg_type in ['interactive', 'image', 'audio', 'voice']:
        thread = threading.Thread(target=_ejecutar_ciclo_agente, args=(data,), daemon=True)
        thread.start()
        return

    text = data.get('text', '').strip()
    if not text:
        return

    with DEBOUNCE_LOCK:
        if clean_phone in DEBOUNCE_BUFFERS:
            entry = DEBOUNCE_BUFFERS[clean_phone]
            old_timer = entry.get('timer')
            if old_timer:
                old_timer.cancel()
            entry['texts'].append(text)
            if data.get('quoted_wamid'):
                entry['data']['quoted_wamid'] = data.get('quoted_wamid')
                entry['data']['raw_msg'] = data.get('raw_msg')
        else:
            DEBOUNCE_BUFFERS[clean_phone] = {
                'texts': [text],
                'data': dict(data),
                'timer': None
            }

        timer = threading.Timer(DEBOUNCE_WINDOW_SECONDS, _flush_debounced_message, args=[clean_phone])
        DEBOUNCE_BUFFERS[clean_phone]['timer'] = timer
        timer.start()

def _ejecutar_ciclo_agente(data: dict):
    from ..models import ConversacionWhatsApp, MensajeWhatsAppLog
    from core.models import Usuario

    phone = data.get('phone')
    text = data.get('text', '').strip()
    if not phone or not text:
        return

    config = get_asistente_config()
    telefono_duena = config.get('telefono_duena', '').replace('+', '').replace(' ', '').replace('-', '')
    clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
    print(f"[ASISTENTE CICLO INICIADO] Mensaje de {clean_phone}: '{text}'", flush=True)

    # 1. Obtener o crear Conversacion
    conversacion, _ = ConversacionWhatsApp.objects.get_or_create(telefono=clean_phone)

    # 2. Vincular usuario si aun no esta vinculado
    if not conversacion.usuario:
        from ..tools.gestion_tools import buscar_usuario_por_telefono
        usuario = buscar_usuario_por_telefono(clean_phone)
        if usuario:
            conversacion.usuario = usuario

    # 3. Detectar rol (reconocimiento automático de Débora, Staff y Profesores)
    from ..config_loader import es_telefono_staff_o_duena
    es_staff_db = False
    if conversacion.usuario:
        es_staff_db = (
            getattr(conversacion.usuario, 'is_staff', False) or
            getattr(conversacion.usuario, 'is_superuser', False) or
            str(getattr(conversacion.usuario, 'rol', '')).upper() in ['ADMIN', 'DUENA', 'DIRECTORA', 'STAFF']
        )

    if es_telefono_staff_o_duena(clean_phone) or es_staff_db:
        conversacion.rol_detectado = 'DUENA'
    elif conversacion.metadata.get('propuesta_ficha_alumna'):
        conversacion.rol_detectado = 'DUENA'
    else:
        is_profesor = False
        if conversacion.usuario:
            is_profesor = getattr(conversacion.usuario, 'is_profesor', False) or str(getattr(conversacion.usuario, 'rol', '')).upper() == 'PROFESOR'
        if not is_profesor:
            try:
                from plugins.profesores.backend.models import Profesor
                from django.db.models import Q
                p_obj = Profesor.objects.filter(is_active=True).filter(
                    Q(telefono__icontains=clean_phone[-8:]) |
                    Q(usuario__telefono__icontains=clean_phone[-8:])
                ).first()
                if p_obj:
                    is_profesor = True
                    if not conversacion.usuario and p_obj.usuario:
                        conversacion.usuario = p_obj.usuario
            except Exception:
                pass

        if is_profesor:
            conversacion.rol_detectado = 'PROFESOR'
        elif conversacion.usuario:
            conversacion.rol_detectado = 'ALUMNA'
        else:
            conversacion.rol_detectado = 'PROSPECTO'

    # 3.1 Recuperar contexto si la usuaria respondió citando un mensaje de WhatsApp
    raw_msg = data.get('raw_msg', {})
    quoted_wamid = data.get('quoted_wamid') or (raw_msg.get('context', {}).get('id') if isinstance(raw_msg, dict) else None)
    texto_citado = None
    if quoted_wamid:
        wamid_map = conversacion.metadata.get('sent_wamid_map', {})
        texto_citado = wamid_map.get(quoted_wamid)

    # 3.2 Si no citó explícitamente pero es Débora/Staff respondiendo a una alerta reciente de agenda
    if not texto_citado and conversacion.rol_detectado == 'DUENA':
        import datetime
        hace_20m = timezone.now() - datetime.timedelta(minutes=20)
        ultimo_aviso = conversacion.mensajes.filter(
            direccion='SALIENTE',
            created_at__gte=hace_20m
        ).order_by('-created_at').first()
        if ultimo_aviso and any(k in ultimo_aviso.texto.lower() for k in ['alerta', 'solo 1 alumna', 'aviso dirección', 'camillas libres']):
            text_low = text.lower()
            if any(k in text_low for k in ['ese horario', 'esa clase', 'agrega a', 'agregale a', 'agrégale a', 'anota a', 'anotá a', 'pone como profesora', 'poné como profesora', 'cancelala', 'cancelá esa', 'hola no', 'y esta esta']):
                texto_citado = ultimo_aviso.texto

    # 3.3 Si es una profesora respondiendo a una consulta de asistencia activa
    if not texto_citado and conversacion.rol_detectado == 'PROFESOR':
        consulta_activa = conversacion.metadata.get('consulta_asistencia_activa')
        if consulta_activa:
            hora_c = consulta_activa.get('hora', '')
            clase_c = consulta_activa.get('clase_nombre', '')
            alumnas_c = [a.get('nombre') for a in consulta_activa.get('alumnas', []) if a.get('nombre')]
            alumnas_txt = ", ".join(alumnas_c)
            t_id = consulta_activa.get('turno_id', '')
            texto_citado = f"Asistencia de clase {clase_c} ({hora_c} hs) - Alumnas anotadas: {alumnas_txt}. Turno ID: {t_id}"

    # 3.4 Si hay una propuesta de sincronización de ficha física pendiente
    if conversacion.metadata.get('propuesta_ficha_alumna'):
        prop = conversacion.metadata.get('propuesta_ficha_alumna')
        nom_al = prop.get('usuario_nombre', 'la alumna')
        tot_cl = prop.get('total_clases', 0)
        aviso_ficha = (
            f"[INSTRUCCIÓN CRÍTICA DE GESTIÓN: Hay una propuesta de sincronización de ficha física de '{nom_al}' "
            f"({tot_cl} clases) esperando confirmación. Si el mensaje del usuario aprueba, confirma, dice 'sí', 'confirmar', 'dale', 'guardalo', 'exactamente' "
            f"o lo pide por audio, llamá INMEDIATAMENTE a la herramienta 'confirmar_sincronizacion_ficha_duena(decision=\"CONFIRMAR\")'. "
            f"Si cancela o descarta, llamá a 'confirmar_sincronizacion_ficha_duena(decision=\"CANCELAR\")'.]"
        )
        if texto_citado:
            texto_para_agente = f"{aviso_ficha}\n[En respuesta a tu aviso anterior: \"{texto_citado}\"]\n{text}"
        else:
            texto_para_agente = f"{aviso_ficha}\n{text}"
    else:
        texto_para_agente = f'[En respuesta a tu aviso anterior: "{texto_citado}"]\n{text}' if texto_citado else text

    conversacion.save()

    # 4. Registrar log del mensaje entrante
    es_audio = data.get('es_audio', False)
    texto_base = f"🎤 [Audio]: {text}" if es_audio else text
    if texto_citado:
        primera_linea = texto_citado.split('\n')[0][:80]
        texto_log = f"↩️ [En respuesta a: \"{primera_linea}...\"]\n{texto_base}"
    else:
        texto_log = texto_base

    MensajeWhatsAppLog.objects.create(
        conversacion=conversacion,
        direccion='ENTRANTE',
        agente_responsable='usuario',
        texto=texto_log
    )

    # 5. Si la conversación está pausada para atención humana, no responder automáticamente
    if conversacion.estado == 'ESPERANDO_HUMANO':
        logger.info(f"[ASISTENTE] Conversación con {clean_phone} en ESPERANDO_HUMANO. No se genera respuesta automática.")
        return

    # 5.1 Estado de acuse previo:
    # Para audios, audio_service ya envió el acuse inmediato al recibir la nota de voz.
    # Para textos, el orquestador (builder.py) gestiona un temporizador inteligente que SOLO
    # envía acuse si la consulta demora más de 2.5s, evitando spam en respuestas rápidas o saludos.
    ack_enviado = bool(es_audio)

    # 6. Ejecutar Orquestador LangGraph (o simulador de tools)
    try:
        from ..graph.runner import ejecutar_grafo_asistente
        respuesta_texto, agente_responsable, tools_usadas = ejecutar_grafo_asistente(
            conversacion=conversacion,
            mensaje_usuario=texto_para_agente,
            ack_enviado=ack_enviado
        )
    except Exception as e:
        print(f"[ASISTENTE ERROR GRAFO] Excepción para {clean_phone}: {e}", flush=True)
        logger.error(f"[ASISTENTE ERROR] Excepción ejecutando LangGraph para {clean_phone}: {e}", exc_info=True)
        from .debugger_service import registrar_y_diagnosticar_error
        respuesta_texto, _ = registrar_y_diagnosticar_error(
            conversacion=conversacion,
            mensaje_usuario=text,
            excepcion=e,
            agente_responsable="fallback_error"
        )
        agente_responsable = "centinela_debugger"
        tools_usadas = []

    # Sanitizar formato nativo de WhatsApp (eliminar ###, convertir tablas y ** a *)
    try:
        from .formatter import sanitizar_para_whatsapp
        respuesta_texto = sanitizar_para_whatsapp(respuesta_texto)
    except Exception as e:
        logger.warning(f"[ASISTENTE] Error sanitizando mensaje para WhatsApp: {e}")

    # 7. Registrar mensaje saliente en el log
    MensajeWhatsAppLog.objects.create(
        conversacion=conversacion,
        direccion='SALIENTE',
        agente_responsable=agente_responsable,
        texto=respuesta_texto,
        tools_ejecutadas=tools_usadas
    )

    # 8. Despachar a WhatsApp
    print(f"[ASISTENTE DESPACHANDO RESPUESTA] De: {agente_responsable} -> A: {clean_phone} -> '{respuesta_texto[:60]}...'", flush=True)
    client = WhatsAppClient()
    client.send_text_message(clean_phone, respuesta_texto)
    logger.info(f"[ASISTENTE] Mensaje respondido a {clean_phone} por {agente_responsable}: {respuesta_texto[:60]}...")
