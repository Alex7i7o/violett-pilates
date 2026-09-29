import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { toast } from 'sonner';

const PUBLIC_VAPID_KEY = "BFRmOlPUpoJqyhBHnxdg8haRkqH-hEK77Z7kRNRtwDVb3L83ycG61jVucWeZE3jpPh2daoVo7HOfSLh61qby3vI";

function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/**
 * Performs the full subscribe + server-save cycle.
 * Always unsubscribes first to force a fresh subscription object,
 * so even if the browser already has one, we re-register it with the server.
 */
async function doSubscribe(): Promise<boolean> {
  console.log('[Push] Step 1: Requesting notification permission...');
  const permission = await Notification.requestPermission();
  console.log('[Push] Permission result:', permission);
  if (permission !== 'granted') {
    toast.error("Permiso denegado. Activalo en la configuracion del navegador.");
    return false;
  }

  console.log('[Push] Step 2: Waiting for service worker...');
  const registration = await navigator.serviceWorker.ready;
  console.log('[Push] SW ready. Scope:', registration.scope);

  // Always unsubscribe first so we get a fresh, clean subscription
  // This ensures the endpoint saved in our DB is always in sync with the browser
  const existing = await registration.pushManager.getSubscription();
  if (existing) {
    console.log('[Push] Unsubscribing old subscription first...');
    await existing.unsubscribe();
  }

  console.log('[Push] Step 3: Subscribing to Google FCM...');
  let sub: PushSubscription;
  try {
    sub = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(PUBLIC_VAPID_KEY)
    });
    console.log('[Push] New subscription endpoint:', sub.endpoint.substring(0, 80) + '...');
  } catch (err: any) {
    console.error('[Push] pushManager.subscribe() FAILED:', err.name, err.message);
    toast.error("Error al conectar con el servicio de notificaciones de Google.");
    return false;
  }

  const p256dh = btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(sub.getKey('p256dh')!))));
  const auth = btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(sub.getKey('auth')!))));

  console.log('[Push] Step 4: Saving subscription in Violett server...');
  try {
    const res = await api.post('/webpush/subscribe/', {
      endpoint: sub.endpoint,
      keys: { p256dh, auth }
    });
    console.log('[Push] Server saved subscription:', res.data);
  } catch (apiErr: any) {
    console.error('[Push] /webpush/subscribe/ FAILED:', apiErr.response?.status, apiErr.response?.data || apiErr.message);
    toast.error("Error al guardar la suscripcion en el servidor.");
    return false;
  }

  return true;
}

export function usePushNotifications() {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      setIsSupported(true);
      checkSubscription();
    } else {
      console.warn('[Push] serviceWorker or PushManager not supported.');
    }
  }, []);

  const checkSubscription = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      console.log('[Push] SW scope:', registration.scope);
      const sub = await registration.pushManager.getSubscription();
      if (sub) {
        console.log('[Push] Already subscribed:', sub.endpoint.substring(0, 60) + '...');
        setIsSubscribed(true);
      } else {
        console.log('[Push] Not subscribed yet.');
      }
    } catch (e) {
      console.error('[Push] Error checking subscription:', e);
    }
  };

  const subscribe = async () => {
    if (!isSupported) {
      toast.error("Notificaciones no soportadas en este navegador.");
      return;
    }
    try {
      const ok = await doSubscribe();
      if (ok) {
        setIsSubscribed(true);
        // Welcome push fires from the server after 2s
      }
    } catch (e: any) {
      console.error('[Push] Unexpected error:', e);
      toast.error("Error inesperado. Revisa la consola.");
    }
  };

  // Re-run the full subscribe flow even if already subscribed
  // Use this to fix desync between browser and server
  const reactivate = async () => {
    if (!isSupported) return;
    toast.info("Reactivando notificaciones...");
    try {
      const ok = await doSubscribe();
      if (ok) {
        setIsSubscribed(true);
        toast.success("Notificaciones reactivadas! Deberia llegarte una de prueba en segundos.");
      }
    } catch (e: any) {
      console.error('[Push] Unexpected error during reactivate:', e);
      toast.error("Error inesperado. Revisa la consola.");
    }
  };

  const testPush = async () => {
    try {
      console.log('[Push] Triggering test push...');
      const res = await api.get('/webpush/test/');
      console.log('[Push] Test push response:', res.data);
      toast.info("Notificacion de prueba enviada. Espera unos segundos...");
    } catch (e: any) {
      console.error('[Push] Test push failed:', e.response?.data || e.message);
      toast.error("Error al disparar notificacion de prueba.");
    }
  };

  return {
    isSupported,
    isSubscribed,
    subscribe,
    reactivate,
    testPush,
  };
}