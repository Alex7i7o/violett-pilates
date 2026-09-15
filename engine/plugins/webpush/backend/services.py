import json
import logging
from .models import PushSubscription

logger = logging.getLogger(__name__)

def send_webpush(usuario, title, body, data=None):
    '''
    Sends a web push notification to all subscriptions of a user.
    In local development, this acts as a simulator.
    '''
    subs = PushSubscription.objects.filter(usuario=usuario)
    if not subs.exists():
        logger.info(f"[WebPush Simulator] No subscriptions for user {usuario.email}")
        return

    for sub in subs:
        payload = {
            'title': title,
            'body': body,
            'data': data or {}
        }
        # In a real app we would use pywebpush here
        # from pywebpush import webpush, WebPushException
        # webpush(subscription_info, json.dumps(payload), VAPID_PRIVATE_KEY, VAPID_CLAIMS)
        
        logger.info(f"[WebPush Simulator] Sent push to {usuario.email} at {sub.endpoint}: {json.dumps(payload)}")