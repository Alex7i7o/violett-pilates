import { useState, useEffect } from 'react';

export function useInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if running in standalone mode (already installed)
    const checkStandalone = () => {
      const isStan = window.matchMedia('(display-mode: standalone)').matches || 
                     (window.navigator as any).standalone === true;
      setIsStandalone(isStan);
    };
    checkStandalone();

    // Check if device is iOS
    const ua = window.navigator.userAgent;
    const isIosDevice = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    setIsIOS(isIosDevice);

    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const promptInstall = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        setDeferredPrompt(null);
      }
    }
  };

  return { deferredPrompt, isIOS, isStandalone, promptInstall };
}
