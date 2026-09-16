import React, { useState } from 'react';
import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useInstallPrompt } from '../../../frontend/src/hooks/useInstallPrompt';
import { BookingFunnel } from './views/BookingFunnel';
import { ClientDashboard } from './views/ClientDashboard';
import { TiendaPaquetes } from './views/TiendaPaquetes';
import { ResenasClient } from './views/ResenasClient';
import { useClientProfile } from '@/hooks/useClientProfile';
import { LogOut, Calendar, Wallet, Store, Star, User } from 'lucide-react';
import { api } from '@/lib/api';

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
    initial: { opacity: 0, y: 15, scale: 0.98 },
    enter: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.4, ease: [0.23, 1, 0.32, 1] } },
    exit: { opacity: 0, y: -10, scale: 0.98, transition: { duration: 0.2, ease: "easeIn" } }
  };

  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col font-sans pb-[env(safe-area-inset-bottom)]">

      {/* Desktop Header */}
        <header className="hidden sm:flex bg-white/80 backdrop-blur-xl border-b border-neutral-200 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 h-16 w-full flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-primary-main tracking-tight">
            Violett
          </Link>
          <nav className="flex items-center gap-6">
            {!isStandalone && (deferredPrompt || isIOS) && (
              <button onClick={promptInstall} className="text-sm font-bold text-white bg-primary-main px-4 py-1.5 rounded-full hover:bg-primary-hover transition-colors shadow-sm">
                {isIOS ? "Instalar App" : "Instalar App"}
              </button>
            )}
            {navItems.map(item => {
              const active = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <Link 
                  key={item.path}
                  to={item.path} 
                  className={`flex items-center gap-2 text-sm font-semibold transition-colors ${active ? 'text-primary-main' : 'text-neutral-500 hover:text-neutral-900'}`}
                >
                  <item.icon size={18} strokeWidth={active ? 2.5 : 2} />
                  <span>{item.name}</span>
                </Link>
              );
            })}

            <div className="w-px h-6 bg-neutral-200 mx-2"></div>

            <button onClick={handleLogout} className="flex items-center gap-2 text-sm font-semibold text-rose-600 hover:text-rose-700 transition-colors" title="Cerrar Sesión">
              <LogOut size={18} strokeWidth={2.5} />
            </button>
          </nav>
        </div>
      </header>

      {/* Mobile Top Header */}
      <header className="sm:hidden flex items-center justify-between px-5 h-16 bg-neutral-50 z-40 sticky top-0">
         <span className="text-2xl font-bold text-neutral-900 tracking-tight flex items-center gap-2">
            {navItems.find(item => location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path)))?.name || 'Violett'}
         </span>
         <div className="flex items-center gap-3">
           {!isStandalone && (deferredPrompt || isIOS) && (
             <button onClick={promptInstall} className="text-xs font-bold text-primary-main bg-primary-light/30 px-3 py-1.5 rounded-full border border-primary-main/20 active:bg-primary-light/50 transition-colors">
               Instalar
             </button>
           )}
           <button onClick={handleLogout} className="p-2 rounded-full bg-white shadow-sm text-rose-500 border border-neutral-100 active:scale-95 transition-transform">
             <LogOut size={18} strokeWidth={2.5} />
           </button>
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
      <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-[20px] saturate-[180%] border-t border-neutral-200/60 pb-[env(safe-area-inset-bottom)]">
        <div className="flex items-center justify-around px-2 h-16">
          {navItems.map((item) => {
            const active = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${active ? 'text-primary-main' : 'text-neutral-400 active:scale-95 transition-transform'}`}
              >
                <item.icon size={22} strokeWidth={active ? 2.5 : 2} />
                <span className="text-[10px] font-semibold">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>

    </div>
  );
};

