import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Home, Calendar as CalendarIcon, User as UserIcon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { InstallAppModal } from '../components/ui/InstallAppModal';
import { useClientConfig } from '../context/ClientConfigContext';

export function ClientLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const config = useClientConfig();
  const isEstetica = config.client_id === 'violett_estetica';

  const tabs = [
    { path: '/', label: 'Inicio', icon: Home },
    { path: '/mis-reservas', label: 'Reservas', icon: CalendarIcon },
    { path: '/perfil', label: 'Perfil', icon: UserIcon },
  ];

  return (
    <div className="flex flex-col min-h-[100dvh] bg-background">
      <InstallAppModal />
      <header className="hidden md:flex bg-white/60 backdrop-blur-[20px] saturate-[180%] border-b border-primary-light/40 shadow-sm sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between w-full">
          <div className="flex items-center gap-3">
            <img src={isEstetica ? "/logo-estetica-icon.png" : "/logo-icon.png"} alt="Violett" className="h-12 object-contain drop-shadow-sm" />
            <div className="flex flex-col justify-center">
               <span className="font-bold text-lg text-primary-main tracking-tight leading-tight">{isEstetica ? 'Panel de Pacientes' : 'Panel de Alumnas'}</span>
               <span className="text-xs font-semibold text-violett-400 uppercase tracking-widest leading-none">{isEstetica ? 'Violett Estética' : 'Violett Pilates'}</span>
            </div>
          </div>
          <nav className="flex gap-1 bg-muted/10 p-1 rounded-xl">
            {tabs.map(tab => {
              const active = location.pathname === tab.path;
              return (
                <button
                  key={tab.path}
                  onClick={() => navigate(tab.path)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${active ? 'bg-white shadow-sm text-primary-main' : 'text-muted hover:text-foreground'}`}
                >
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>
      </header>

      <main className="flex-1 w-full relative overflow-x-hidden md:p-8 pb-[calc(80px+env(safe-area-inset-bottom))] md:pb-8">
        <motion.div
            key={location.pathname}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0, transition: { duration: 0.2, ease: "easeOut" } }}
            className="h-full"
        >
            <Outlet />
        </motion.div>
      </main>

      <nav className="flex md:hidden fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-2xl border-t border-primary-light/40 z-40 pb-safe">
        <div className="flex w-full justify-around items-center h-[60px]">
          {tabs.map(tab => {
            const active = location.pathname === tab.path;
            const Icon = tab.icon;
            return (
              <button
                key={tab.path}
                onClick={() => navigate(tab.path)}
                className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${active ? 'text-primary-main' : 'text-muted active:scale-95 transition-transform'}`}
              >
                <Icon className="w-6 h-6" strokeWidth={active ? 2.5 : 2} />
                <span className="text-[10px] font-medium">{tab.label}</span>
              </button>
            )
          })}
        </div>
      </nav>
    </div>
  );
}
