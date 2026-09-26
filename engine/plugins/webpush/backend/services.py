import json
import logging
from .models import PushSubscription
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = "HELAhHxLk377Cj8FPjWh_HSRAe7hoIHVFm68sOVE17E"
VAPID_CLAIMS = {
    "sub": "mailto:hola@violett.com.ar"
}

def send_webpush(usuario, title, body, data=None):
    '''
    Sends a web push notification to all subscriptions of a user.
    '''
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
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            logger.info(f"[WebPush OK] Sent push to {usuario.email} at {sub.endpoint}")
        except WebPushException as ex:
            logger.error(f"[WebPush ERROR] {ex}")
            if ex.response and ex.response.status_code in [404, 410]:
                logger.info(f"Subscription expired or invalid for {usuario.email}, deleting.")
                sub.delete()
        except Exception as e:
            logger.error(f"[WebPush EXCEPTION] {e}")

