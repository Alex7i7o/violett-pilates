import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { toast } from 'sonner';

// Clave pública VAPID (Ejemplo para desarrollo)
const PUBLIC_VAPID_KEY = "BDv-xW7-Xy5Z0m_9C8H4GjN6pLqL2UeO_fK3y1S_1gE_M3WdJ7Y5wT6yI7YxK6x2Z9L3wN1P8Q1V5O9K3X2G4R8=";

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
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      setIsSupported(true);
      checkSubscription();
    }
  }, []);

  const checkSubscription = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const sub = await registration.pushManager.getSubscription();
      if (sub) {
        setIsSubscribed(true);
        setSubscription(sub);
      }
    } catch (e) {
      console.error('Error checking subscription', e);
    }
  };

  const subscribe = async () => {
    if (!isSupported) return toast.error("Notificaciones no soportadas en este navegador.");
    
    try {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        toast.error("Permiso de notificaciones denegado.");
        return;
      }

      const registration = await navigator.serviceWorker.ready;
      const sub = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(PUBLIC_VAPID_KEY)
      });

      const p256dh = btoa(String.fromCharCode.apply(null, new Uint8Array(sub.getKey('p256dh')!)));
      const auth = btoa(String.fromCharCode.apply(null, new Uint8Array(sub.getKey('auth')!)));

      await api.post('/webpush/subscribe/', {
        endpoint: sub.endpoint,
        keys: { p256dh, auth }
      });

      setIsSubscribed(true);
      setSubscription(sub);
      toast.success("¡Notificaciones activadas!");
    } catch (e) {
      console.error('Failed to subscribe:', e);
      toast.error("Error al activar notificaciones.");
    }
  };

  return {
    isSupported,
    isSubscribed,
    subscription,
    subscribe
  };
}