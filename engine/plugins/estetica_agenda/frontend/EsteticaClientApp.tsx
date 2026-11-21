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
  primaryMain: "#150720",
  primarySurface: "#240E34",
  primaryHover: "#35144C",
  primaryLight: "#F5E9DF",
  accentMain: "#C5A059",
  accentHover: "#B38E4C",
  accentAmber: "#D4AF37",
  accentGlow: "rgba(197, 160, 89, 0.35)",
  techPeriwinkle: "#C084FC",
  creamSilk: "#FFF8EE",
  background: "#0D0414",
  card: "#190826",
  foreground: "#FFF8EE",
  border: "rgba(197, 160, 89, 0.22)"
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
    <FireSeedProvider theme={esteticaThemeTokens} className="min-h-screen bg-[#0D0414] text-[#FFF8EE] flex flex-col font-sans pb-[env(safe-area-inset-bottom)] selection:bg-[#C5A059]/30 selection:text-[#FFF8EE]">

      {/* Desktop Luxury Header */}
      <header className="hidden sm:flex bg-[#150720]/80 backdrop-blur-xl border-b border-[#C5A059]/20 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 h-16 w-full flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#C5A059] to-[#E5C788] flex items-center justify-center text-[#150720] shadow-md shadow-[#C5A059]/20 group-hover:scale-105 transition-transform">
              <Sparkles size={16} strokeWidth={2.5} />
            </span>
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight text-[#FFF8EE] font-serif">
                Violett
              </span>
              <span className="text-[10px] uppercase tracking-widest text-[#C5A059] font-semibold -mt-1">
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
                className="text-xs !bg-[#C5A059] !text-[#150720] hover:!bg-[#B38E4C]"
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
                  onClick={() => haptics.selection()}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                    active
                      ? 'bg-[#C5A059]/15 text-[#C5A059] border border-[#C5A059]/30 shadow-sm'
                      : 'text-[#FFF8EE]/60 hover:text-[#FFF8EE] hover:bg-white/5'
                  }`}
                >
                  <item.icon size={15} strokeWidth={active ? 2.5 : 2} />
                  <span>{item.name}</span>
                </Link>
              );
            })}

            <div className="w-px h-5 bg-white/10 mx-1"></div>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
              title="Cerrar Sesión"
            >
              <LogOut size={16} strokeWidth={2.5} />
            </Button>
          </nav>
        </div>
      </header>

      {/* Mobile Top Header */}
      <header className="sm:hidden flex items-center justify-between px-5 h-16 bg-[#150720]/90 backdrop-blur-md border-b border-[#C5A059]/15 z-40 sticky top-0">
        <div className="flex items-center gap-2.5">
          <span className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#C5A059] to-[#E5C788] flex items-center justify-center text-[#150720] shadow-sm">
            <Sparkles size={14} strokeWidth={2.5} />
          </span>
          <span className="text-lg font-bold text-[#FFF8EE] tracking-tight font-serif">
            {navItems.find(item => location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path)))?.name || 'Violett Estética'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {!isStandalone && (deferredPrompt || isIOS) && (
            <Button
              variant="glow"
              size="sm"
              onClick={promptInstall}
              className="text-[11px] h-8 px-2.5 !bg-[#C5A059] !text-[#150720]"
            >
              Instalar
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={handleLogout}
            className="text-rose-400 hover:bg-rose-500/10 w-9 h-9"
          >
            <LogOut size={16} strokeWidth={2.5} />
          </Button>
        </div>
      </header>

      <main className="flex-1 w-full max-w-4xl mx-auto px-4 pb-24 sm:pb-8 sm:pt-8 relative">
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
      <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#150720]/90 backdrop-blur-[20px] saturate-[180%] border-t border-[#C5A059]/20 pb-[env(safe-area-inset-bottom)]">
        <div className="flex items-center justify-around px-2 h-16">
          {navItems.map((item) => {
            const active = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={() => haptics.selection()}
                className={`flex flex-col items-center justify-center w-full h-full space-y-1 transition-transform active:scale-95 ${
                  active ? 'text-[#C5A059]' : 'text-[#FFF8EE]/50 hover:text-[#FFF8EE]'
                }`}
              >
                <item.icon size={20} strokeWidth={active ? 2.5 : 2} />
                <span className="text-[10px] font-semibold">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>

    </FireSeedProvider>
  );
};

