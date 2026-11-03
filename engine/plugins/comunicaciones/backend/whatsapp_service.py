import logging
import os
import requests

logger = logging.getLogger(__name__)

class WhatsAppClient:
    def __init__(self):
        # En prod se leen de variables de entorno
        self.token = os.environ.get('WHATSAPP_TOKEN')
        self.phone_number_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
        self.base_url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        self.is_configured = bool(self.token and self.phone_number_id)

    def _send_template(self, to_number, template_name, components, language_code="es_AR"):
        if not self.is_configured:
            print(f"\n[WHATSAPP SIMULATOR] Plantilla '{template_name}' a {to_number} (Variables: {components})\n", flush=True)
            from backend_core.hooks import registry
            registry.execute('wpp_enviado_tracker', {})
            return True

        if not to_number:
            print("[WHATSAPP ERROR] to_number vacío para plantilla", flush=True)
            return False
            
        phone = str(to_number).replace("+", "").replace("-", "").replace(" ", "")

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                },
                "components": components
            }
        }
        
        try:
            print(f"[WHATSAPP ENVIANDO PLANTILLA] '{template_name}' (Lang: {language_code}) a {phone}", flush=True)
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                print(f"[WHATSAPP PLANTILLA ENVIADA EXITOSAMENTE] Status: {response.status_code} a {phone}", flush=True)
                from backend_core.hooks import registry
                registry.execute('wpp_enviado_tracker', {})
                return True
            else:
                if language_code == "es_AR" and "language" in response.text.lower():
                    print("[WHATSAPP PLANTILLA] Idioma es_AR no disponible. Reintentando con 'es'...", flush=True)
                    payload["template"]["language"]["code"] = "es"
                    res2 = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
                    if res2.status_code in [200, 201]:
                        print(f"[WHATSAPP PLANTILLA ENVIADA CON 'es'] Status: {res2.status_code}", flush=True)
                        from backend_core.hooks import registry
                        registry.execute('wpp_enviado_tracker', {})
                        return True

                print(f"[WHATSAPP ERROR META PLANTILLA] Status: {response.status_code} | Respuesta: {response.text}", flush=True)
                logger.error(f"[WHATSAPP ERROR] {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"[WHATSAPP EXCEPTION PLANTILLA] {e}", flush=True)
            logger.error(f"[WHATSAPP EXCEPTION] {e}")
            return False

    def download_media_bytes(self, media_id: str):
        """Descarga el binario de una imagen o documento desde Meta WhatsApp Cloud API"""
        if not self.is_configured or not media_id:
            return None
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            res = requests.get(f"https://graph.facebook.com/v19.0/{media_id}", headers=headers, timeout=10)
            if res.status_code != 200:
                logger.error(f"[WHATSAPP MEDIA URL ERROR] {res.status_code} - {res.text}")
                return None
            media_url = res.json().get('url')
            if not media_url:
                return None
            file_res = requests.get(media_url, headers=headers, timeout=15)
            if file_res.status_code == 200:
                return file_res.content
            logger.error(f"[WHATSAPP MEDIA DOWNLOAD ERROR] {file_res.status_code}")
            return None
        except Exception as e:
            logger.error(f"[WHATSAPP MEDIA EXCEPTION] {e}")
            return None


    def mark_as_read(self, message_id: str):
        '''Marca un mensaje entrante como leído en WhatsApp (doble tilde azul)'''
        if not self.is_configured or not message_id:
            return False
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'messaging_product': 'whatsapp',
            'status': 'read',
            'message_id': message_id
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=5)
            return response.status_code in [200, 201]
        except Exception:
            return False

    def send_text_message(self, to_number, text_message):
        '''Envia un mensaje de texto libre (solo funciona dentro de la ventana de 24hs iniciada por el usuario)'''
        try:
            from plugins.asistente.backend.services.formatter import sanitizar_para_whatsapp
            text_message = sanitizar_para_whatsapp(text_message)
        except Exception:
            pass
        if not self.is_configured:
            print(f"\n[WHATSAPP NO CONFIGURADO / SIMULADOR] (WHATSAPP_TOKEN o WHATSAPP_PHONE_NUMBER_ID vacios en el contenedor)", flush=True)
            print(f"-> Destino: {to_number}", flush=True)
            print(f"-> Mensaje: {text_message}\n", flush=True)
            from backend_core.hooks import registry
            registry.execute('wpp_enviado_tracker', {})
            return True

        if not to_number:
            print("[WHATSAPP ERROR] to_number vacio", flush=True)
            return False

        phone = str(to_number).replace('+', '').replace('-', '').replace(' ', '')

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': phone,
            'type': 'text',
            'text': {
                'preview_url': False,
                'body': text_message
            }
        }

        try:
            print(f'[WHATSAPP ENVIANDO A META] URL: {self.base_url} | Destino: {phone}', flush=True)
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                print(f'[WHATSAPP ENVIADO EXITOSAMENTE] Status: {response.status_code} | Respuesta: {response.text}', flush=True)
                from backend_core.hooks import registry
                registry.execute('wpp_enviado_tracker', {})
                return True
            else:
                print(f'[WHATSAPP ERROR META] Status: {response.status_code} | Respuesta: {response.text}', flush=True)
                logger.error(f'[WHATSAPP TEXT ERROR] {response.status_code} - {response.text}')
                return False
        except Exception as e:
            print(f'[WHATSAPP EXCEPTION] {e}', flush=True)
            logger.error(f'[WHATSAPP TEXT EXCEPTION] {e}')
            return False
def _registrar_log_saliente(phone, usuario, texto, agente="notificaciones_sistema"):
    try:
        from plugins.asistente.backend.models import ConversacionWhatsApp, MensajeWhatsAppLog
        clean_phone = str(phone).replace("+", "").replace("-", "").replace(" ", "")
        conv = ConversacionWhatsApp.objects.filter(telefono=clean_phone).first()
        if not conv and clean_phone:
            conv = ConversacionWhatsApp.objects.create(
                telefono=clean_phone,
                usuario=usuario,
                rol_detectado='ALUMNA'
            )
        if conv:
            MensajeWhatsAppLog.objects.create(
                conversacion=conv,
                direccion='SALIENTE',
                agente_responsable=agente,
                texto=texto
            )
    except Exception as e:
        logger.warning(f"Error registrando log de notificacion WhatsApp: {e}")

def notificar_cancelacion_clase(usuario, turno):
    client = WhatsAppClient()
    if not usuario:
        return
    phone = getattr(usuario, 'telefono', None)
    if not phone:
        return

    nombre = usuario.nombre.split()[0] if usuario.nombre else "Alumna"
    clase_nom = turno.clase.nombre if turno.clase else "Pilates Reformer"
    fecha_str = turno.fecha.strftime('%d/%m')
    hora_str = turno.hora_inicio.strftime('%H:%M')
    texto = (
        f"¡Hola {nombre}! ✦ Te avisamos desde Violett Pilates que la clase de "
        f"*{clase_nom}* del *{fecha_str} a las {hora_str} hs* fue cancelada por la administración. "
        f"El crédito ya fue reintegrado a tu plan activo 🌸."
    )
    enviado = client.send_text_message(phone, texto)
    if not enviado:
        components = [{
            "type": "body",
            "parameters": [
                {"type": "text", "text": usuario.nombre},
                {"type": "text", "text": f"{clase_nom} ({turno.fecha})"},
                {"type": "text", "text": "El crédito ha sido devuelto a tu plan."}
            ]
        }]
        client._send_template(phone, "clase_cancelada_admin", components)
    _registrar_log_saliente(phone, usuario, texto, "notificacion_clase_cancelada")

def notificar_reserva_creada(usuario, turno):
    client = WhatsAppClient()
    if not usuario:
        return
    phone = getattr(usuario, 'telefono', None)
    if not phone:
        return

    nombre = usuario.nombre.split()[0] if usuario.nombre else "Alumna"
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nombre = dias_semana[turno.fecha.weekday()]
    fecha_str = turno.fecha.strftime('%d/%m')
    hora_str = turno.hora_inicio.strftime('%H:%M')
    clase_nombre = turno.clase.nombre if turno.clase else "Pilates Reformer"

    profe_txt = ""
    try:
        from plugins.asistente.backend.tools.profesores_tools import obtener_profesor_de_turno
        prof = obtener_profesor_de_turno(turno)
        if prof and hasattr(prof, 'nombre'):
            profe_txt = f" con la Profe {prof.nombre}"
    except Exception:
        pass

    texto = (
        f"¡Hola {nombre}! ✦ Te confirmamos desde Violett Pilates que quedaste agendada para tu clase de "
        f"*{clase_nombre}* el *{dia_nombre} {fecha_str} a las {hora_str} hs*{profe_txt} 🌸.\n\n"
        f"¡Te esperamos en el estudio para disfrutar de tu momento de bienestar!"
    )
    enviado = client.send_text_message(phone, texto)
    if not enviado:
        components = [{
            "type": "body",
            "parameters": [
                {"type": "text", "text": usuario.nombre},
                {"type": "text", "text": clase_nombre},
                {"type": "text", "text": hora_str}
            ]
        }]
        client._send_template(phone, "reserva_confirmada", components)
    _registrar_log_saliente(phone, usuario, texto, "notificacion_reserva_creada")
    try:
        notificar_duena_reserva(usuario, turno)
    except Exception as ex_d:
        logger.warning(f"Error notificando reserva a la dueña: {ex_d}")

def notificar_cancelacion_usuario(usuario, turno, motivo=""):
    client = WhatsAppClient()
    if not usuario:
        return
    phone = getattr(usuario, 'telefono', None)
    if not phone:
        return

    nombre = usuario.nombre.split()[0] if usuario.nombre else "Alumna"
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nombre = dias_semana[turno.fecha.weekday()]
    fecha_str = turno.fecha.strftime('%d/%m')
    hora_str = turno.hora_inicio.strftime('%H:%M')
    clase_nombre = turno.clase.nombre if turno.clase else "Pilates Reformer"

    motivo_txt = f" ({motivo})" if motivo else ""
    texto = (
        f"¡Hola {nombre}! ✦ Te avisamos desde Violett Pilates que tu turno de *{clase_nombre}* "
        f"del *{dia_nombre} {fecha_str} a las {hora_str} hs* fue cancelado{motivo_txt}. "
        f"El crédito correspondiente ya se encuentra disponible en tu plan para cuando desees volver a agendarte 🌿."
    )
    enviado = client.send_text_message(phone, texto)
    if not enviado:
        components = [{
            "type": "body",
            "parameters": [
                {"type": "text", "text": usuario.nombre},
                {"type": "text", "text": f"{clase_nombre} el {turno.fecha}"}
            ]
        }]
        client._send_template(phone, "reserva_cancelada_usuario", components)
    _registrar_log_saliente(phone, usuario, texto, "notificacion_cancelacion_usuario")
    try:
        notificar_duena_cancelacion(usuario, turno, motivo)
    except Exception as ex_d:
        logger.warning(f"Error notificando cancelacion a la dueña: {ex_d}")

def notificar_reprogramacion_alumna(usuario, turno_nuevo, turno_anterior=None):
    client = WhatsAppClient()
    if not usuario:
        return
    phone = getattr(usuario, 'telefono', None)
    if not phone:
        return

    nombre = usuario.nombre.split()[0] if usuario.nombre else "Alumna"
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nombre = dias_semana[turno_nuevo.fecha.weekday()]
    fecha_str = turno_nuevo.fecha.strftime('%d/%m')
    hora_str = turno_nuevo.hora_inicio.strftime('%H:%M')
    clase_nombre = turno_nuevo.clase.nombre if turno_nuevo.clase else "Pilates Reformer"

    profe_txt = ""
    try:
        from plugins.asistente.backend.tools.profesores_tools import obtener_profesor_de_turno
        prof = obtener_profesor_de_turno(turno_nuevo)
        if prof and hasattr(prof, 'nombre'):
            profe_txt = f" con la Profe {prof.nombre}"
    except Exception:
        pass

    cambio_de = ""
    if turno_anterior:
        d_ant = dias_semana[turno_anterior.fecha.weekday()]
        cambio_de = f" de las {turno_anterior.hora_inicio.strftime('%H:%M')} hs ({d_ant} {turno_anterior.fecha.strftime('%d/%m')})"

    texto = (
        f"¡Hola {nombre}! ✦ Te avisamos desde Violett Pilates que tu clase{cambio_de} fue modificada.\n\n"
        f"Tu nuevo horario confirmado es: *{dia_nombre} {fecha_str} a las {hora_str} hs* ({clase_nombre}){profe_txt} ✦.\n\n"
        f"Cualquier consulta o si necesitás cambiarlo, estamos a tu disposición 🌸."
    )
    enviado = client.send_text_message(phone, texto)
    if not enviado:
        components = [{
            "type": "body",
            "parameters": [
                {"type": "text", "text": usuario.nombre},
                {"type": "text", "text": clase_nombre},
                {"type": "text", "text": f"{dia_nombre} {fecha_str} {hora_str} hs"}
            ]
        }]
        client._send_template(phone, "reserva_confirmada", components)
    _registrar_log_saliente(phone, usuario, texto, "notificacion_reprogramacion_alumna")
    try:
        notificar_duena_reprogramacion(usuario, turno_nuevo, turno_anterior)
    except Exception as ex_d:
        logger.warning(f"Error notificando reprogramacion a la dueña: {ex_d}")

def notificar_horario_fijo_alumna(usuario, dia_semana: int, hora_str: str, clase_nombre: str = "Pilates Reformer", profe_nombre: str = "", accion: str = "asignado"):
    client = WhatsAppClient()
    if not usuario:
        return
    phone = getattr(usuario, 'telefono', None)
    if not phone:
        return

    nombre = usuario.nombre.split()[0] if usuario.nombre else "Alumna"
    dias_es = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
    dia_nombre = dias_es.get(dia_semana, f"Día {dia_semana}")
    profe_txt = f" con la Profe {profe_nombre}" if profe_nombre else ""

    if accion == "dada_de_baja":
        texto = (
            f"¡Hola {nombre}! ✦ Te avisamos desde Violett Pilates que tu horario fijo de los "
            f"*{dia_nombre}s a las {hora_str} hs* fue dado de baja 🌿.\n\n"
            f"Podés seguir reservando tus turnos individuales con los créditos de tu abono siempre que quieras."
        )
    else:
        texto = (
            f"¡Hola {nombre}! ✦ Te avisamos desde Violett Pilates que tenés un nuevo horario fijo semanal asignado:\n\n"
            f"• *Todos los {dia_nombre}s a las {hora_str} hs* - {clase_nombre}{profe_txt} ✦.\n\n"
            f"Ya dejamos todas tus camillas reservadas automáticamente para cada semana. ¡Te esperamos! 🌸"
        )
    client.send_text_message(phone, texto)
    _registrar_log_saliente(phone, usuario, texto, "notificacion_horario_fijo_alumna")

def obtener_telefono_duena():
    try:
        from plugins.asistente.backend.config_loader import get_asistente_config
        config = get_asistente_config()
        tel = config.get('telefono_duena', '5491157691786')
        return str(tel).replace('+', '').replace('-', '').replace(' ', '')
    except Exception:
        return '5491157691786'

def notificar_duena_reserva(usuario, turno):
    tel_duena = obtener_telefono_duena()
    if not tel_duena:
        return

    # Evitar auto-notificarse si la reserva es de la misma dueña
    tel_user = getattr(usuario, 'telefono', '') if usuario else ''
    if tel_user and str(tel_user).replace('+', '').replace('-', '').replace(' ', '') == tel_duena:
        return

    nombre_alumna = f"{usuario.nombre} {usuario.apellido}".strip() if usuario else "Una alumna"
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nombre = dias_semana[turno.fecha.weekday()]
    fecha_str = turno.fecha.strftime('%d/%m')
    hora_str = turno.hora_inicio.strftime('%H:%M')
    clase_nom = turno.clase.nombre if turno.clase else "Pilates Reformer"
    cupo_libres = turno.cupo_actual

    profe_txt = ""
    try:
        from plugins.asistente.backend.tools.profesores_tools import obtener_profesor_de_turno
        prof = obtener_profesor_de_turno(turno)
        if prof and hasattr(prof, 'nombre'):
            profe_txt = f" con Profe {prof.nombre}"
    except Exception:
        pass

    msg_duena = (
        f"✦ *Aviso Dirección - Reserva* ✦\n\n"
        f"• *Alumna:* {nombre_alumna} se agendó\n"
        f"• *Clase:* {dia_nombre} {fecha_str} a las {hora_str} hs ({clase_nom}){profe_txt}\n"
        f"• *Camillas disponibles:* {cupo_libres} libres."
    )

    client = WhatsAppClient()
    client.send_text_message(tel_duena, msg_duena)
    _registrar_log_saliente(tel_duena, None, msg_duena, "notificacion_duena")

def notificar_duena_cancelacion(usuario, turno, motivo=""):
    tel_duena = obtener_telefono_duena()
    if not tel_duena:
        return

    tel_user = getattr(usuario, 'telefono', '') if usuario else ''
    if tel_user and str(tel_user).replace('+', '').replace('-', '').replace(' ', '') == tel_duena:
        return

    nombre_alumna = f"{usuario.nombre} {usuario.apellido}".strip() if usuario else "Una alumna"
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nombre = dias_semana[turno.fecha.weekday()]
    fecha_str = turno.fecha.strftime('%d/%m')
    hora_str = turno.hora_inicio.strftime('%H:%M')
    clase_nom = turno.clase.nombre if turno.clase else "Pilates Reformer"
    cupo_libres = turno.cupo_actual

    motivo_str = f"\n• *Motivo:* {motivo}" if motivo else ""
    msg_duena = (
        f"✦ *Aviso Dirección - Baja de Clase* ✦\n\n"
        f"• *Alumna:* {nombre_alumna} se dio de baja\n"
        f"• *Clase:* {dia_nombre} {fecha_str} a las {hora_str} hs ({clase_nom}){motivo_str}\n"
        f"• *Camilla liberada:* Ahora hay {cupo_libres} libres en ese bloque."
    )

    client = WhatsAppClient()
    client.send_text_message(tel_duena, msg_duena)
    _registrar_log_saliente(tel_duena, None, msg_duena, "notificacion_duena")

def notificar_duena_reprogramacion(usuario, turno_nuevo, turno_anterior=None):
    tel_duena = obtener_telefono_duena()
    if not tel_duena:
        return

    tel_user = getattr(usuario, 'telefono', '') if usuario else ''
    if tel_user and str(tel_user).replace('+', '').replace('-', '').replace(' ', '') == tel_duena:
        return

    nombre_alumna = f"{usuario.nombre} {usuario.apellido}".strip() if usuario else "Una alumna"
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nuevo_nom = dias_semana[turno_nuevo.fecha.weekday()]
    fecha_nueva_str = turno_nuevo.fecha.strftime('%d/%m')
    hora_nueva_str = turno_nuevo.hora_inicio.strftime('%H:%M')
    clase_nom = turno_nuevo.clase.nombre if turno_nuevo.clase else "Pilates Reformer"

    ant_str = ""
    if turno_anterior:
        dia_ant_nom = dias_semana[turno_anterior.fecha.weekday()]
        fecha_ant_str = turno_anterior.fecha.strftime('%d/%m')
        hora_ant_str = turno_anterior.hora_inicio.strftime('%H:%M')
        ant_str = f"• *Se dio de baja de:* {dia_ant_nom} {fecha_ant_str} a las {hora_ant_str} hs (camilla liberada)\n"

    msg_duena = (
        f"✦ *Aviso Dirección - Modificación de Horario* ✦\n\n"
        f"• *Alumna:* {nombre_alumna} modificó su clase\n"
        f"{ant_str}"
        f"• *Se agendó para:* {dia_nuevo_nom} {fecha_nueva_str} a las {hora_nueva_str} hs ({clase_nom})\n"
        f"• *Camillas disponibles:* {turno_nuevo.cupo_actual} libres."
    )

    client = WhatsAppClient()
    client.send_text_message(tel_duena, msg_duena)
    _registrar_log_saliente(tel_duena, None, msg_duena, "notificacion_duena")
