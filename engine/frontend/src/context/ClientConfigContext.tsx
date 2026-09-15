import React, { createContext, useContext, useEffect, useState } from 'react';

export interface ClientConfig {
  client_id: string;
  business_name: string;
  domain: string;
  theme: {
    primary_main: string;
    primary_hover: string;
    primary_light: string;
    text_foreground: string;
    border_radius: string;
  };
  features: {
    online_payments: boolean;
    class_packs: boolean;
    client_registration: boolean;
    whatsapp_reminders: boolean;
  };
  active_plugins: string[];
  copywriting: {
    hero_title: string;
    hero_subtitle: string;
    cta_login: string;
  };
}

const ClientConfigContext = createContext<ClientConfig | null>(null);

export function useClientConfig() {
  const context = useContext(ClientConfigContext);
  if (!context) {
    throw new Error('useClientConfig must be used within a ClientConfigProvider');
  }
  return context;
}

export function ClientConfigProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<ClientConfig | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const baseUrl = import.meta.env.BASE_URL || '/';
    const configPath = baseUrl.endsWith('/') ? baseUrl + 'client-config.json' : baseUrl + '/client-config.json';
    fetch(configPath)
      .then((res) => {
        if (!res.ok) throw new Error('No se pudo cargar la configuracion del cliente');
        return res.json();
      })
      .then((data: ClientConfig) => {
        setConfig(data);
        const root = document.documentElement;
        root.style.setProperty('--color-primary-main', data.theme.primary_main);
        root.style.setProperty('--color-primary-hover', data.theme.primary_hover);
        root.style.setProperty('--color-primary-light', data.theme.primary_light);
        root.style.setProperty('--color-text-foreground', data.theme.text_foreground);
        root.style.setProperty('--radius-card', data.theme.border_radius);
                document.title = data.business_name;
          if (data.client_id === 'violett_estetica') {
            const icons = document.querySelectorAll('link[rel="icon"]');
            icons.forEach(icon => {
              icon.setAttribute('href', '/logo-estetica-icon.png');
            });
            const appleIcon = document.querySelector('link[rel="apple-touch-icon"]');
            if (appleIcon) {
              appleIcon.setAttribute('href', '/logo-estetica-icon.png');
            }
          }

      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
      });
  }, []);

  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-500 font-bold">{error}</div>;
  }

  if (!config) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  return (
    <ClientConfigContext.Provider value={config}>
      {children}
    </ClientConfigContext.Provider>
  );
}
