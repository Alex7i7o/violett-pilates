import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/lib/api';
import { Calendar, Briefcase, User, Menu, X, LogOut, CheckCircle2 } from 'lucide-react';

export function ProfesorLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const hash = location.hash || '#hoy';


  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);
  const [hasNewBolsa, setHasNewBolsa] = useState(false);

  useEffect(() => {
    const checkBolsa = async () => {
      try {
        const res = await api.get('/profesor/dashboard/');
        const totalUnassigned = res.data.turnos_libres.length + res.data.plantillas_libres.length;
        const lastSeen = parseInt(localStorage.getItem('last_seen_bolsa') || '0');
        if (totalUnassigned > lastSeen) {
          setHasNewBolsa(true);
        }
      } catch (e) {}
    };
    checkBolsa();
  }, []);

  useEffect(() => {
    if (hash === '#bolsa') {
      setHasNewBolsa(false);
      api.get('/profesor/dashboard/').then(res => {
        const totalUnassigned = res.data.turnos_libres.length + res.data.plantillas_libres.length;
        localStorage.setItem('last_seen_bolsa', totalUnassigned.toString());
      }).catch(() => {});
    }
  }, [hash]);


  useEffect(() => { 
    setIsMoreMenuOpen(false); 
  }, [location.pathname, location.hash]);

  const handleLogout = async () => {
    const baseUrl = import.meta.env.BASE_URL || '/';
    const loginPath = baseUrl.endsWith('/') ? baseUrl + 'login' : baseUrl + '/login';
    try {
      await api.post('/auth/logout/');
    } catch (e) {
      console.error(e);
    } finally {
      window.location.href = loginPath;
    }
  };

  const mobileTabs = [
    { id: '#hoy', name: 'Hoy', icon: CheckCircle2 },
    { id: '#agenda', name: 'Agenda', icon: Calendar },
    { id: '#bolsa', name: 'Bolsa', icon: Briefcase },
  ];

  return (
    <div className="flex flex-col min-h-[100dvh] bg-background font-sans">
      
      {/* Mobile Header */}
      <header className="lg:hidden flex items-center justify-between px-4 py-4 bg-white/80 backdrop-blur-[20px] saturate-[180%] border-b border-primary-light/40 sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary-main flex items-center justify-center text-white font-bold italic text-sm">V</div>
          <span className="font-bold text-lg text-primary-main tracking-tight">Staff</span>
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-white text-xs font-bold shadow-sm">P</div>
      </header>

      {/* Desktop Header */}
      <header className="hidden lg:flex bg-white/70 backdrop-blur-xl saturate-150 border-b border-primary-light/50 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-8 h-16 flex items-center justify-between w-full">
          <div className="flex items-center">
            <div className="flex items-center gap-2"><img src="/logo-icon.png" alt="Violett Pilates" className="h-14 object-contain" /> <span className="text-violett-400 font-bold text-lg md:text-xl leading-none">Staff</span></div>
          </div>
          <nav className="flex items-center gap-4">
            <button onClick={handleLogout} className="flex items-center gap-2 text-sm font-medium text-rose-600 hover:text-rose-700 transition-colors">
              <LogOut className="w-4 h-4" />
              Cerrar Sesión
            </button>
          </nav>
        </div>
      </header>
      
      {/* Main Content Area */}
      <main className="flex-1 w-full relative overflow-x-hidden p-4 lg:p-8 pb-[calc(80px+env(safe-area-inset-bottom))] lg:pb-8 max-w-7xl mx-auto">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div 
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.32, 0.72, 0, 1] } }}
            exit={{ opacity: 0, transition: { duration: 0.15 } }}
            className="h-full"
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Mobile Bottom Tab Bar */}
      <nav className="flex lg:hidden fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-2xl border-t border-primary-light/40 z-40 pb-safe">
        <div className="flex w-full justify-around items-center h-[60px]">
          {mobileTabs.map((tab) => {
            const isActive = hash === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => navigate(tab.id, { replace: true })}
                className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${isActive ? 'text-primary-main' : 'text-muted active:scale-95 transition-transform'}`}
              >
                <div className="relative">
                  <Icon className="w-6 h-6" strokeWidth={isActive ? 2.5 : 2} />
                  {tab.id === '#bolsa' && hasNewBolsa && (
                    <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-red-500 border-2 border-white rounded-full animate-pulse"></span>
                  )}
                </div>
                <span className="text-[10px] font-medium">{tab.name}</span>
              </button>
            );
          })}
          
          {/* Mobile Profile / More Menu Button */}
          <button
            onClick={() => navigate('#perfil', { replace: true })}
            className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${hash === '#perfil' ? 'text-primary-main' : 'text-muted active:scale-95 transition-transform'}`}
          >
            <User className="w-6 h-6" strokeWidth={hash === '#perfil' ? 2.5 : 2} />
            <span className="text-[10px] font-medium">Perfil</span>
          </button>
        </div>
      </nav>
    </div>
  );
}
