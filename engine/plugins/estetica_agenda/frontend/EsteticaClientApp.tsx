import React from 'react';
import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { FireSeedProvider, Button, haptics } from 'fireseed-ui';
import { useInstallPrompt } from '../../../frontend/src/hooks/useInstallPrompt';
import { BookingFunnel } from './views/BookingFunnel';
import { ClientDashboard } from './views/ClientDashboard';
import { TiendaPaquetes } from './views/TiendaPaquetes';
import { ResenasClient } from './views/ResenasClient';
import { useClientProfile } from '@/hooks/useClientProfile';
import { LogOut, Calendar, Wallet, Store, Star, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';

const esteticaThemeTokens = {
  primaryMain: "#34236F",
  primarySurface: "#FFFFFF",
  primaryHover: "#2A1C5A",
  primaryLight: "#F9F6ED",
  accentMain: "#C5A059",
  accentHover: "#B38E4C",
  accentAmber: "#D4AF37",
  accentGlow: "rgba(197, 160, 89, 0.25)",
  techPeriwinkle: "#34236F",
  creamSilk: "#FFFFFF",
  background: "#FAFAFA",
  card: "#FFFFFF",
  foreground: "#34236F",
  border: "rgba(197, 160, 89, 0.25)"
};

export const EsteticaClientApp = () => {
  const { profile } = useClientProfile();
  const location = useLocation();
  const { deferredPrompt, isIOS, isStandalone, promptInstall } = useInstallPrompt();

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/');
    } finally {
      window.location.href = (import.meta.env.BASE_URL || '/') + 'login';
    }
  };

  const navItems = [
    { name: 'Reservar', path: '/', icon: Calendar },
    { name: 'Billetera', path: '/mi-cuenta', icon: Wallet },
    { name: 'Tienda', path: '/tienda', icon: Store },
    { name: 'Reseñas', path: '/resenas', icon: Star },
  ];

  const pageVariants = {
    initial: { opacity: 0, y: 12, scale: 0.99 },
    enter: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.35, ease: [0.23, 1, 0.32, 1] } },
    exit: { opacity: 0, y: -8, scale: 0.99, transition: { duration: 0.2, ease: "easeIn" } }
  };

  return (
    <FireSeedProvider theme={esteticaThemeTokens} className="min-h-screen bg-[#FAFAFA] text-[#34236F] flex flex-col font-sans pb-[env(safe-area-inset-bottom)] selection:bg-[#C5A059]/20 selection:text-[#34236F]">

      {/* Desktop Header */}
      <header className="hidden sm:flex bg-white/90 backdrop-blur-xl border-b border-neutral-200/80 sticky top-0 z-50 shadow-xs">
        <div className="max-w-4xl mx-auto px-6 h-16 w-full flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <img src="/logo-estetica-icon.png" alt="Violett Estética" className="h-9 w-auto object-contain" />
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight text-[#34236F] font-serif">
                Violett
              </span>
              <span className="text-[10px] uppercase tracking-widest text-[#C5A059] font-bold -mt-1">
                Estética & Bienestar
              </span>
            </div>
          </Link>

          <nav className="flex items-center gap-4">
            {!isStandalone && (deferredPrompt || isIOS) && (
              <Button
                variant="glow"
                size="sm"
                onClick={promptInstall}
                className="text-xs !bg-[#C5A059] !text-white hover:!bg-[#B38E4C] rounded-full px-4"
              >
                Instalar App
              </Button>
            )}

            {navItems.map(item => {
              const active = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => haptics.light()}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                    active
                      ? 'bg-[#C5A059]/15 text-[#C5A059] border border-[#C5A059]/30 shadow-xs'
                      : 'text-neutral-500 hover:text-[#34236F] hover:bg-neutral-100/80'
                  }`}
                >
                  <item.icon size={15} strokeWidth={active ? 2.5 : 2} />
                  <span>{item.name}</span>
                </Link>
              );
            })}

            <div className="w-px h-5 bg-neutral-200 mx-1"></div>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-rose-500 hover:text-rose-600 hover:bg-rose-50"
              title="Cerrar Sesión"
            >
              <LogOut size={16} strokeWidth={2.5} />
            </Button>
          </nav>
        </div>
      </header>

      {/* Mobile Top Header */}
      <header className="sm:hidden flex items-center justify-between px-5 h-16 bg-white/95 backdrop-blur-md border-b border-neutral-200/80 z-40 sticky top-0 shadow-xs">
        <div className="flex items-center gap-2.5">
          <img src="/logo-estetica-icon.png" alt="Violett Estética" className="h-8 w-auto object-contain" />
          <span className="text-lg font-bold text-[#34236F] tracking-tight font-serif">
            {navItems.find(item => location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path)))?.name || 'Violett Estética'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {!isStandalone && (deferredPrompt || isIOS) && (
            <Button
              variant="glow"
              size="sm"
              onClick={promptInstall}
              className="text-[11px] h-8 px-2.5 !bg-[#C5A059] !text-white"
            >
              Instalar
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={handleLogout}
            className="text-rose-500 hover:bg-rose-50 w-9 h-9"
          >
            <LogOut size={16} strokeWidth={2.5} />
          </Button>
        </div>
      </header>

      <main className="flex-1 w-full max-w-4xl mx-auto px-3 sm:px-6 pb-24 sm:pb-8 sm:pt-8 relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial="initial"
            animate="enter"
            exit="exit"
            variants={pageVariants}
            className="w-full"
          >
            <Routes location={location}>
              <Route path="/" element={<BookingFunnel />} />
              <Route path="/mi-cuenta" element={<ClientDashboard />} />
              <Route path="/tienda" element={<TiendaPaquetes />} />
              <Route path="/resenas" element={<ResenasClient />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Mobile Bottom Tab Bar */}
      <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-[20px] saturate-[180%] border-t border-neutral-200/80 pb-[env(safe-area-inset-bottom)] shadow-lg">
        <div className="flex items-center justify-around px-2 h-16">
          {navItems.map((item) => {
            const active = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={() => haptics.light()}
                className={`flex flex-col items-center justify-center w-full h-full space-y-1 transition-transform active:scale-95 ${
                  active ? 'text-[#C5A059] font-bold' : 'text-neutral-400 hover:text-neutral-600'
                }`}
              >
                <item.icon size={20} strokeWidth={active ? 2.5 : 2} />
                <span className="text-[10px]">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>

    </FireSeedProvider>
  );
};