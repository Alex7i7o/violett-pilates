import React, { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';
import { getPluginAdminSidebarItems } from '../core/pluginLoader';
import { useClientConfig } from '../context/ClientConfigContext';
import { Calendar, Users, LayoutList, Menu, X, CreditCard, UserSquare, Layers, LogOut, Settings } from 'lucide-react';

export function AdminLayout() {
  const navigate = useNavigate();
  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);
  const location = useLocation();
  const config = useClientConfig();
  const isEstetica = config.client_id === 'violett_estetica';
  
  useEffect(() => { 
    setIsMoreMenuOpen(false); 
  }, [location.pathname]);

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

  const pluginItems = getPluginAdminSidebarItems();

  let baseNavItems = [
    { name: 'Agenda', path: '/admin/agenda', icon: Calendar },
    { name: 'Clases', path: '/admin/clases', icon: LayoutList },
    { name: isEstetica ? 'Pacientes' : 'Alumnos', path: '/admin/alumnos', icon: Users },
    { name: 'Profesores', path: '/admin/profesores', icon: UserSquare },
    { name: 'Planes', path: '/admin/planes', icon: CreditCard },
    { name: 'Esquema', path: '/admin/esquema', icon: Layers },
    { name: 'Reglas de Negocio', path: '/admin/reglas', icon: Settings }
  ];

  if (isEstetica) {
    baseNavItems = baseNavItems.filter(item => !['Clases', 'Profesores', 'Planes', 'Esquema'].includes(item.name));
  } else {
    baseNavItems = baseNavItems.filter(item => !['Reglas de Negocio'].includes(item.name));
  }

  const allNavItems = [
    ...baseNavItems,
    ...pluginItems.filter(p => isEstetica || (!p.path.includes('estetica') && p.name !== 'Servicios' && p.name !== 'Paquetes' && p.name !== 'Horarios Estetica')).map(p => ({ ...p, icon: p.icon || Layers }))
  ];

  // Primary tabs for mobile bottom bar
  const primaryTabs = allNavItems.slice(0, 3);
  
  // Secondary items for the "More" menu
  const secondaryItems = allNavItems.slice(3);

  return (
    <div className="flex flex-col min-h-[100dvh] bg-background font-sans">
      
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-64 shrink-0 bg-card border-r border-primary-light flex-col fixed top-0 bottom-0 overflow-y-auto custom-scrollbar z-50">
        <div className="p-6 pb-2">
          <div className="flex flex-col items-center mb-4 mt-2">
            <img src={isEstetica ? "/logo-estetica-full.png" : "/logo-full.png"} alt="Violett" className="h-20 object-contain mx-auto" />
            <span className="font-bold text-lg text-primary-main tracking-tight">Panel de Negocio</span>
          </div>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mt-4">Panel de Negocio</h2>
        </div>
        <nav className="flex-1 mt-4">
          <ul className="flex flex-col gap-1 px-3">
            {allNavItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path);
              const Icon = item.icon as any;
              return (
                <li key={item.name}>
                  <Link
                    to={item.path}
                    className={`flex items-center gap-3 py-3 px-4 rounded-xl text-sm transition-all ${
                      isActive 
                        ? 'text-primary-main font-bold bg-primary-light shadow-sm' 
                        : 'text-muted hover:bg-primary-light/50 hover:text-foreground'
                    }`}
                  >
                    <Icon className="w-5 h-5" strokeWidth={isActive ? 2.5 : 2} />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        
        <div className="flex-1 flex flex-col justify-end items-center pb-8 opacity-20 pointer-events-none">
          <img src={isEstetica ? "/logo-estetica-icon.png" : "/logo-icon.png"} alt="Violett Isotipo" className="w-40 h-40 object-contain drop-shadow-lg" />
        </div>

        <div className="p-4 border-t border-primary-light">
          <button 
            onClick={handleLogout}
            className="flex items-center gap-3 w-full py-3 px-4 text-sm font-medium text-rose-600 hover:bg-rose-50 rounded-xl transition-colors text-left"
          >
            <LogOut className="w-5 h-5" />
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>
      {/* End Sidebar (desktop) */}
      <div className="flex-1 lg:ml-64 flex flex-col relative overflow-x-hidden">
        
        {/* Mobile Header */}
        <header className="lg:hidden flex items-center justify-between px-4 py-4 bg-white/80 backdrop-blur-[20px] saturate-[180%] border-b border-primary-light/40 sticky top-0 z-40">
          <div className="flex items-center gap-2">
            <img src={isEstetica ? "/logo-estetica-icon.png" : "/logo-icon.png"} alt="Violett" className="h-8 object-contain" />
            <span className="font-bold text-base text-primary-main tracking-tight">Panel de Negocio</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-white text-xs font-bold shadow-sm">A</div>
        </header>

        {/* Desktop Header */}
        <header className="hidden lg:flex items-center justify-end px-8 py-4 bg-background sticky top-0 z-40">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-muted">Admin Team</span>
            <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center text-white text-sm font-bold shadow-sm">A</div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 lg:p-8 pb-[calc(80px+env(safe-area-inset-bottom))] lg:pb-8 max-w-7xl mx-auto w-full">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div 
              key={location.pathname}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0, transition: { duration: 0.3, ease: "easeOut" } }}
              exit={{ opacity: 0, x: -20, transition: { duration: 0.2, ease: "easeIn" } }}
              className="h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Mobile Bottom Tab Bar */}
      <nav className="flex lg:hidden fixed bottom-0 left-0 right-0 bg-white/80 backdrop-blur-2xl border-t border-primary-light/40 z-40 pb-safe">
        <div className="flex w-full justify-around items-center h-[60px]">
          {primaryTabs.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            const Icon = item.icon as any;
            return (
              <button
                key={item.name}
                onClick={() => navigate(item.path)}
                className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${isActive ? 'text-primary-main' : 'text-muted active:scale-95 transition-transform'}`}
              >
                <Icon className="w-6 h-6" strokeWidth={isActive ? 2.5 : 2} />
                <span className="text-[10px] font-medium">{item.name}</span>
              </button>
            );
          })}
          
          {/* Menu Button */}
          <button
            onClick={() => setIsMoreMenuOpen(true)}
            className={`flex flex-col items-center justify-center w-full h-full space-y-1 ${isMoreMenuOpen ? 'text-primary-main' : 'text-muted active:scale-95 transition-transform'}`}
          >
            <Menu className="w-6 h-6" strokeWidth={isMoreMenuOpen ? 2.5 : 2} />
            <span className="text-[10px] font-medium">Más</span>
          </button>
        </div>
      </nav>

      {/* Mobile "More" Bottom Sheet */}
      <AnimatePresence>
        {isMoreMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMoreMenuOpen(false)}
              className="fixed inset-0 bg-black/40 z-50 lg:hidden backdrop-blur-sm"
            />
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', bounce: 0, duration: 0.4 }}
              className="fixed bottom-0 left-0 right-0 bg-card rounded-t-3xl z-50 flex flex-col pb-safe lg:hidden max-h-[85vh]"
            >
              <div className="flex justify-center p-3">
                <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
              </div>
              
              <div className="px-6 pb-2 flex justify-between items-center">
                <h2 className="text-xl font-bold text-foreground">Menú Principal</h2>
                <button onClick={() => setIsMoreMenuOpen(false)} className="p-2 bg-muted/10 rounded-full text-muted hover:text-foreground">
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="overflow-y-auto px-4 py-4 space-y-2">
                {secondaryItems.map((item) => {
                  const isActive = location.pathname.startsWith(item.path);
                  const Icon = item.icon as any;
                  return (
                    <button
                      key={item.name}
                      onClick={() => {
                        navigate(item.path);
                        setIsMoreMenuOpen(false);
                      }}
                      className={`flex items-center gap-4 w-full p-4 rounded-2xl transition-all ${
                        isActive ? 'bg-primary-light text-primary-main font-bold' : 'bg-muted/5 text-foreground active:scale-[0.98]'
                      }`}
                    >
                      <div className={`p-2 rounded-xl ${isActive ? 'bg-white shadow-sm' : 'bg-background'}`}>
                        <Icon className="w-5 h-5" strokeWidth={isActive ? 2.5 : 2} />
                      </div>
                      <span className="text-base">{item.name}</span>
                    </button>
                  );
                })}

                <div className="pt-4 mt-4 border-t border-primary-light/40">
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-4 w-full p-4 rounded-2xl bg-rose-50 text-rose-600 font-medium active:scale-[0.98] transition-transform"
                  >
                    <div className="p-2 rounded-xl bg-white shadow-sm">
                      <LogOut className="w-5 h-5" />
                    </div>
                    <span className="text-base">Cerrar Sesión</span>
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
