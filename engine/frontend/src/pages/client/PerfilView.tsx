import React, { useState } from 'react';
import { useClientProfile } from '../../hooks/useClientProfile';
import { ClientProfileHeader } from '../../components/dashboard/ClientProfileHeader';
import { api } from '../../lib/api';
import { Button } from '../../components/ui/Button';
import { LogOut, Bell } from 'lucide-react';
import { usePushNotifications } from '../../hooks/usePushNotifications';
import { useClientConfig } from '../../context/ClientConfigContext';

export function PerfilView() {
  const { profile, refetch } = useClientProfile();
  const config = useClientConfig();
  const { isSupported, isSubscribed, subscribe } = usePushNotifications();

  const handleLogout = async () => {
    const baseUrl = import.meta.env.BASE_URL || '/';
    const loginPath = baseUrl.endsWith('/') ? baseUrl + 'login' : baseUrl + '/login';
    try {
      await api.post('/auth/logout/');
    } catch (e) {
      // ignore
    } finally {
      document.body.innerHTML = '';
      window.location.replace(loginPath);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 md:px-0 pt-4 md:pt-0 pb-6 space-y-8">
      <div className="md:hidden mt-2 mb-2">
        <h1 className="text-3xl font-bold text-foreground">Mi Perfil</h1>
      </div>

      {profile && (
        <ClientProfileHeader 
          profile={profile} 
          onPlanUpdate={refetch}
        />
      )}

      {/* Acciones de Perfil */}
      <div className="pt-6 border-t border-primary-light/40">
        {config.features?.webpush && isSupported && !isSubscribed && (
        <Button 
          variant="outline" 
          onClick={subscribe}
          className="w-full text-primary-main border-primary-light hover:bg-primary-light/20 mb-4"
        >
          <Bell className="w-5 h-5 mr-2" />
          Activar Avisos de Turnos Libres
        </Button>
      )}
      <Button 
          variant="outline" 
          onClick={handleLogout}
          className="w-full text-red-600 border-red-200 hover:bg-red-50"
        >
          <LogOut className="w-5 h-5 mr-2" />
          Cerrar Sesión
        </Button>
      </div>
    </div>
  );
}
