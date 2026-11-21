import os
import json
import logging
import datetime
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
KEY_FILE = BASE_DIR / 'google_key.pem'
CRED_CONFIG_FILE = BASE_DIR / 'google_service_account.json'

DEFAULT_CLIENT_EMAIL = "reservas-estetica@reservas-app-486503.iam.gserviceaccount.com"
DEFAULT_CALENDAR_ID = "alexxaguero@gmail.com"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = "America/Argentina/Buenos_Aires"
TZ_OFFSET = "-03:00"


def _get_credentials():
    private_key = os.environ.get('GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY')
    if private_key:
        private_key = private_key.replace('\\r', '').replace('\\n', '\n')
    elif KEY_FILE.exists():
        with open(KEY_FILE, 'r', encoding='utf-8') as f:
            private_key = f.read()

    client_email = os.environ.get('GOOGLE_SERVICE_ACCOUNT_EMAIL')
    if not client_email and CRED_CONFIG_FILE.exists():
        try:
            with open(CRED_CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                client_email = cfg.get('client_email')
        except Exception:
            pass

    if not client_email:
        client_email = DEFAULT_CLIENT_EMAIL

    if not private_key:
        logger.warning("[GOOGLE CALENDAR] No se encontró clave privada para Service Account.")
        return None

    info = {
        "type": "service_account",
        "client_email": client_email,
        "private_key": private_key,
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    try:
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        return creds
    except Exception as e:
        logger.error(f"[GOOGLE CALENDAR] Error inicializando credenciales: {e}")
        return None


def get_calendar_id():
    cal_id = os.environ.get('GOOGLE_CALENDAR_ID')
    if not cal_id and CRED_CONFIG_FILE.exists():
        try:
            with open(CRED_CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                cal_id = cfg.get('calendar_id')
        except Exception:
            pass
    return cal_id or DEFAULT_CALENDAR_ID


def get_calendar_service():
    creds = _get_credentials()
    if not creds:
        return None
    try:
        return build('calendar', 'v3', credentials=creds, cache_discovery=False)
    except Exception as e:
        logger.error(f"[GOOGLE CALENDAR] Error conectando con API Calendar: {e}")
        return None


def crear_evento_calendario(reserva) -> str | None:
    service = get_calendar_service()
    if not service:
        return None

    try:
        cal_id = get_calendar_id()
        paciente = f"{reserva.usuario.nombre or ''} {reserva.usuario.apellido or ''}".strip() or reserva.usuario.email
        summary = f"NUEVO TURNO: {paciente} - {reserva.servicio.nombre}"
        
        hora_inicio_str = str(reserva.hora_inicio)[:8]
        hora_fin_str = str(reserva.hora_fin)[:8]
        start_iso = f"{reserva.fecha.isoformat()}T{hora_inicio_str}{TZ_OFFSET}"
        end_iso = f"{reserva.fecha.isoformat()}T{hora_fin_str}{TZ_OFFSET}"

        desc = (
            f"Paciente: {paciente}\n"
            f"Email: {reserva.usuario.email}\n"
            f"Teléfono: {reserva.usuario.telefono or 'No informado'}\n"
            f"Tratamiento: {reserva.servicio.nombre} ({reserva.servicio.duracion_minutos} min)\n"
            f"Estado: {reserva.estado}\n"
            f"ID Reserva Violett: {str(reserva.id)}"
        )

        body = {
            "summary": summary,
            "description": desc,
            "start": {"dateTime": start_iso, "timeZone": TIMEZONE},
            "end": {"dateTime": end_iso, "timeZone": TIMEZONE},
        }

        created = service.events().insert(calendarId=cal_id, body=body).execute()
        event_id = created.get('id')
        logger.info(f"[GOOGLE CALENDAR] Turno insertado en Google Calendar con ID: {event_id}")
        return event_id
    except Exception as e:
        logger.error(f"[GOOGLE CALENDAR] Error insertando turno en Google Calendar: {e}")
        return None


def actualizar_evento_calendario(reserva) -> bool:
    if not reserva.google_event_id:
        # Si no tenía ID en Google, lo creamos ahora
        new_id = crear_evento_calendario(reserva)
        if new_id:
            reserva.google_event_id = new_id
            reserva.save(update_fields=['google_event_id'])
            return True
        return False

    service = get_calendar_service()
    if not service:
        return False

    try:
        cal_id = get_calendar_id()
        paciente = f"{reserva.usuario.nombre or ''} {reserva.usuario.apellido or ''}".strip() or reserva.usuario.email
        summary = f"TURNO: {paciente} - {reserva.servicio.nombre} [{reserva.estado}]"

        hora_inicio_str = str(reserva.hora_inicio)[:8]
        hora_fin_str = str(reserva.hora_fin)[:8]
        start_iso = f"{reserva.fecha.isoformat()}T{hora_inicio_str}{TZ_OFFSET}"
        end_iso = f"{reserva.fecha.isoformat()}T{hora_fin_str}{TZ_OFFSET}"

        body = {
            "summary": summary,
            "start": {"dateTime": start_iso, "timeZone": TIMEZONE},
            "end": {"dateTime": end_iso, "timeZone": TIMEZONE},
        }

        service.events().patch(calendarId=cal_id, eventId=reserva.google_event_id, body=body).execute()
        logger.info(f"[GOOGLE CALENDAR] Evento {reserva.google_event_id} actualizado.")
        return True
    except Exception as e:
        logger.error(f"[GOOGLE CALENDAR] Error actualizando evento: {e}")
        return False


def cancelar_evento_calendario(reserva) -> bool:
    if not reserva.google_event_id:
        return False

    service = get_calendar_service()
    if not service:
        return False

    try:
        cal_id = get_calendar_id()
        service.events().delete(calendarId=cal_id, eventId=reserva.google_event_id).execute()
        logger.info(f"[GOOGLE CALENDAR] Evento {reserva.google_event_id} eliminado de Calendar.")
        return True
    except Exception as e:
        logger.warning(f"[GOOGLE CALENDAR] No se pudo eliminar evento de Calendar (puede ya estar eliminado): {e}")
        return False


def consultar_ocupados_google(fecha: datetime.date) -> list[tuple[datetime.time, datetime.time]]:
    service = get_calendar_service()
    if not service:
        return []

    try:
        cal_id = get_calendar_id()
        start_dt = datetime.datetime.combine(fecha, datetime.time.min).isoformat() + TZ_OFFSET
        end_dt = datetime.datetime.combine(fecha, datetime.time.max).isoformat() + TZ_OFFSET

        body = {
            "timeMin": start_dt,
            "timeMax": end_dt,
            "timeZone": TIMEZONE,
            "items": [{"id": cal_id}]
        }

        res = service.freebusy().query(body=body).execute()
        busy_items = res.get('calendars', {}).get(cal_id, {}).get('busy', [])

        ocupados = []
        for item in busy_items:
            start_str = item.get('start', '')
            end_str = item.get('end', '')
            if start_str and end_str:
                dt_start = datetime.datetime.fromisoformat(start_str)
                dt_end = datetime.datetime.fromisoformat(end_str)
                ocupados.append((dt_start.time(), dt_end.time()))

        return ocupados
    except Exception as e:
        logger.warning(f"[GOOGLE CALENDAR] Error consultando FreeBusy: {e}")
        return []
