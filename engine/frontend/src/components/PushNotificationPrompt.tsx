import React, { useState, useEffect } from 'react';
import { Bell, X } from 'lucide-react';
import { usePushNotifications } from '../hooks/usePushNotifications';
import { useClientConfig } from '../context/ClientConfigContext';

export function PushNotificationPrompt() {
  const { isSupported, isSubscribed, subscribe } = usePushNotifications();
  const config = useClientConfig();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Only show if supported, not subscribed, feature is enabled, and user hasn't dismissed it
    const dismissed = localStorage.getItem('push_prompt_dismissed');
    if (config.features?.webpush && isSupported && !isSubscribed && !dismissed) {
      // Delay showing the prompt to not overwhelm on initial load
      const timer = setTimeout(() => setIsVisible(true), 2000);
      return () => clearTimeout(timer);
    }
  }, [config.features?.webpush, isSupported, isSubscribed]);

  if (!isVisible) return null;

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem('push_prompt_dismissed', 'true');
  };

  const handleSubscribe = async () => {
    await subscribe();
    setIsVisible(false);
  };

  return (
    <div className="bg-violett-50 border border-violett-200 rounded-2xl p-4 flex items-start sm:items-center justify-between gap-4 shadow-sm animate-fade-in-up">
      <div className="flex items-start sm:items-center gap-3">
        <div className="p-2 bg-violett-100 rounded-full text-violett-600 shrink-0">
          <Bell className="w-5 h-5" />
        </div>
        <div>
          <h4 className="font-semibold text-gray-900 text-sm">Activar Notificaciones</h4>
          <p className="text-sm text-gray-600 mt-0.5">
            Recibí un aviso apenas se libere un cupo en una clase llena o cuando tu clase esté por empezar.
          </p>
        </div>
      </div>
      <div className="flex flex-col sm:flex-row items-center gap-2 shrink-0">
        <button 
          onClick={handleSubscribe}
          className="bg-violett-600 hover:bg-violett-700 text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors whitespace-nowrap w-full sm:w-auto"
        >
          Permitir Avisos
        </button>
        <button 
          onClick={handleDismiss}
          className="p-2 text-gray-400 hover:text-gray-600 transition-colors hidden sm:block"
          aria-label="Cerrar"
        >
          <X className="w-5 h-5" />
        </button>
        <button 
          onClick={handleDismiss}
          className="text-gray-500 text-sm font-medium px-4 py-2 sm:hidden"
        >
          Ahora no
        </button>
      </div>
    </div>
  );
}
