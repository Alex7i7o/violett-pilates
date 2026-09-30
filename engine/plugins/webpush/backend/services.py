import json
import logging
import threading
from .models import PushSubscription
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = "I7b2-6rtWOErgpT6nz7WfwD1KCVVraIVPelGOL1Le4A"
VAPID_CLAIMS = {
    "sub": "mailto:hola@violett.com.ar"
}


def _do_send_webpush(usuario, title, body, data=None):
    """
    Internal function that actually calls pywebpush. Always runs in a background thread.
    """
    subs = PushSubscription.objects.filter(usuario=usuario)
    if not subs.exists():
        logger.info(f"[WebPush] No subscriptions for user {usuario.email}")
        return

    for sub in subs:
        payload = {
            'title': title,
            'body': body,
            'data': data or {}
        }

        try:
            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth
                }
            }
            result = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
                ttl=86400,  # 24 hours TTL
            )
            logger.info(f"[WebPush OK] Sent push to {usuario.email} - status: {result.status_code}")
        except WebPushException as ex:
            response_text = ""
            if ex.response:
                response_text = f" HTTP {ex.response.status_code}: {ex.response.text}"
                if ex.response.status_code in [404, 410]:
                    logger.info(f"[WebPush] Subscription expired for {usuario.email}, deleting.")
                    sub.delete()
            logger.error(f"[WebPush ERROR] {usuario.email}: {ex}{response_text}")
        except Exception as e:
            logger.error(f"[WebPush EXCEPTION] {usuario.email}: {type(e).__name__}: {e}")


def send_webpush(usuario, title, body, data=None):
    """
    Non-blocking: fires webpush in a daemon background thread.
    Safe to call from within a Django request/response cycle.
    """
    t = threading.Thread(
        target=_do_send_webpush,
        args=(usuario, title, body, data),
        daemon=True
    )
    t.start()


def send_webpush_sync(usuario, title, body, data=None):
    """
    Blocking: used only for the TestWebPushView diagnostic endpoint.
    Returns (success: bool, message: str).
    """
    subs = PushSubscription.objects.filter(usuario=usuario)
    if not subs.exists():
        return False, f"No subscriptions found for {usuario.email}"

    results = []
    for sub in subs:
        payload = {
            'title': title,
            'body': body,
            'data': data or {}
        }
        try:
            subscription_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth
                }
            }
            result = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
                ttl=86400,
            )
            results.append(f"OK (HTTP {result.status_code}) endpoint: {sub.endpoint[:60]}...")
        except WebPushException as ex:
            detail = ""
            if ex.response:
                detail = f" HTTP {ex.response.status_code}: {ex.response.text}"
                if ex.response.status_code in [404, 410]:
                    sub.delete()
                    detail += " [subscription deleted]"
            results.append(f"ERROR: {ex}{detail}")
        except Exception as e:
            results.append(f"EXCEPTION {type(e).__name__}: {e}")

    success = any("OK" in r for r in results)
    return success, "\n".join(results)
