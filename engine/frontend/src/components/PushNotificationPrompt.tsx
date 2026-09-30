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
    // Record that they interacted with the prompt so it never bothers them again
    localStorage.setItem('push_prompt_dismissed', 'true');
    await subscribe();
    setIsVisible(false);
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-[100] md:hidden backdrop-blur-sm transition-opacity" onClick={handleDismiss} />
      
      <div className="fixed bottom-0 left-0 right-0 z-[101] bg-white rounded-t-[2rem] p-6 pb-10 shadow-2xl transform transition-transform duration-300 md:static md:bg-white md:border md:border-primary-light md:rounded-2xl md:p-4 md:pb-4 md:shadow-sm md:flex md:items-center md:justify-between md:gap-4 md:mb-6">
        
        {/* Mango (mobile) */}
        <div className="w-12 h-1.5 bg-gray-200 rounded-full mx-auto mb-6 md:hidden"></div>

        <div className="flex items-start md:items-center gap-4">
          <div className="p-3.5 bg-primary-light rounded-2xl text-primary-main shrink-0 md:p-2 md:rounded-full">
            <Bell className="w-6 h-6 md:w-5 md:h-5" />
          </div>
          <div>
            <h4 className="font-bold text-gray-900 text-[1.1rem] md:text-sm">Activar Avisos</h4>
            <p className="text-gray-600 mt-1.5 text-[0.95rem] leading-snug md:text-sm md:mt-0.5">
              Enterate al instante cuando se libera un lugar o tu clase est por empezar.
            </p>
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-center gap-3 mt-8 md:mt-0 md:shrink-0">
          <button 
            onClick={handleSubscribe}
            className="w-full md:w-auto bg-primary-main active:bg-primary-hover text-white text-base md:text-sm font-semibold px-5 py-4 md:py-2 rounded-[1rem] md:rounded-xl transition-colors whitespace-nowrap shadow-lg shadow-primary-light"
          >
            Activar Notificaciones
          </button>
          <button 
            onClick={handleDismiss}
            className="w-full md:w-auto text-gray-500 active:bg-gray-50 text-base md:text-sm font-medium px-5 py-3 md:py-2 rounded-[1rem] md:rounded-xl transition-colors md:hidden"
          >
            Ahora no
          </button>
          
          {/* Close for Desktop */}
          <button 
            onClick={handleDismiss}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors hidden md:block"
            aria-label="Cerrar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
    </>
  );
}
