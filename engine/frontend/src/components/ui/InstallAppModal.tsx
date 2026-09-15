import React, { useEffect, useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { useInstallPrompt } from '../../hooks/useInstallPrompt';
import { Share, Download } from 'lucide-react';

export function InstallAppModal() {
  const { deferredPrompt, isIOS, isStandalone, promptInstall } = useInstallPrompt();
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    // Only show if not installed
    if (isStandalone) return;

    // Only show on mobile devices
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    if (!isMobile) return;

    // Check if we've shown it before
    const hasShown = localStorage.getItem('hasShownInstallPrompt');
    if (!hasShown) {
      // Delay showing the prompt slightly so it doesn't block immediate login flow
      const timer = setTimeout(() => {
        if (deferredPrompt || isIOS) {
          setIsOpen(true);
          localStorage.setItem('hasShownInstallPrompt', 'true');
        }
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [deferredPrompt, isIOS, isStandalone]);

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Instalar App">
      <div className="space-y-6 text-center">
        <div className="bg-primary-light/30 p-6 rounded-2xl inline-block mt-2">
          <Download className="w-12 h-12 text-primary-main mx-auto mb-2" />
          <h3 className="text-xl font-bold text-foreground">Violett Pilates</h3>
        </div>
        
        <p className="text-muted text-sm px-4">
          Instalá la aplicación en tu celular para acceder más rápido, sin bordes del navegador y con notificaciones integradas.
        </p>

        {isIOS ? (
          <div className="bg-muted/10 rounded-xl p-4 text-left text-sm space-y-3">
            <p className="font-semibold text-foreground">En tu iPhone o iPad:</p>
            <ol className="list-decimal pl-5 space-y-2 text-muted">
              <li>Toca el botón <b>Compartir</b> <Share className="inline w-4 h-4 mx-1" /> en la barra de abajo.</li>
              <li>Busca y selecciona <b>"Agregar a Inicio"</b>.</li>
              <li>Toca <b>"Agregar"</b> en la esquina superior derecha.</li>
            </ol>
          </div>
        ) : (
          <Button 
            onClick={() => {
              promptInstall();
              setIsOpen(false);
            }} 
            className="w-full text-lg h-12 rounded-xl"
            disabled={!deferredPrompt}
          >
            Instalar Aplicación
          </Button>
        )}
        
        <button 
          onClick={() => setIsOpen(false)}
          className="text-sm font-medium text-muted hover:text-foreground active:scale-95 transition-transform"
        >
          Quizás más tarde
        </button>
      </div>
    </Modal>
  );
}
