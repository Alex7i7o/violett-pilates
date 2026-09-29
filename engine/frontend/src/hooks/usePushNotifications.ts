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

export function usePushNotifications() {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      setIsSupported(true);
      checkSubscription();
    } else {
      console.warn('[Push] serviceWorker or PushManager not supported in this browser.');
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
      console.log('[Push] Step 1: Requesting notification permission...');
      const permission = await Notification.requestPermission();
      console.log('[Push] Permission result:', permission);

      if (permission !== 'granted') {
        toast.error("Permiso de notificaciones denegado. Activalo desde la configuracion del navegador.");
        return;
      }

      console.log('[Push] Step 2: Waiting for service worker to be ready...');
      const registration = await navigator.serviceWorker.ready;
      console.log('[Push] SW ready. Scope:', registration.scope, '| Active SW:', registration.active?.scriptURL);

      console.log('[Push] Step 3: Subscribing to push with VAPID key...');
      let sub: PushSubscription;
      try {
        sub = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(PUBLIC_VAPID_KEY)
        });
        console.log('[Push] Subscribed! Endpoint:', sub.endpoint.substring(0, 80) + '...');
      } catch (subscribeErr: any) {
        console.error('[Push] pushManager.subscribe() FAILED:', subscribeErr);
        console.error('[Push] Error name:', subscribeErr.name, '| message:', subscribeErr.message);
        toast.error("Error al conectar con Google Push Services. Revisa la consola del navegador.");
        return;
      }

      const p256dh = btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(sub.getKey('p256dh')!))));
      const auth = btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(sub.getKey('auth')!))));

      console.log('[Push] Step 4: Sending subscription to Violett server...');
      try {
        const res = await api.post('/webpush/subscribe/', {
          endpoint: sub.endpoint,
          keys: { p256dh, auth }
        });
        console.log('[Push] Server response:', res.data);
      } catch (apiErr: any) {
        console.error('[Push] API call to /webpush/subscribe/ FAILED:', apiErr.response?.data || apiErr.message);
        toast.error("Error al guardar tu suscripcion en el servidor.");
        return;
      }

      setIsSubscribed(true);
      toast.success("Notificaciones activadas! En unos segundos deberia llegarte una de prueba.");
    } catch (e: any) {
      console.error('[Push] Unexpected error during subscribe():', e);
      toast.error("Error inesperado al activar notificaciones. Revisa la consola.");
    }
  };

  const testPush = async () => {
    try {
      console.log('[Push] Triggering test push sequence...');
      const res = await api.get('/webpush/test/');
      console.log('[Push] Test push started:', res.data);
      toast.info("Secuencia de prueba iniciada. Espera 3 segundos...");
    } catch (e: any) {
      console.error('[Push] Test push failed:', e.response?.data || e.message);
      toast.error("Error al disparar notificacion de prueba.");
    }
  };

  return {
    isSupported,
    isSubscribed,
    subscribe,
    testPush,
  };
}