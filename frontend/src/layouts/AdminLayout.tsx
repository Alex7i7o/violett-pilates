import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';

export function AdminLayout() {
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
  const location = useLocation();
  React.useEffect(() => { setIsMobileMenuOpen(false); }, [location.pathname]);

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/');
      window.location.href = '/login';
    } catch (e) {
      window.location.href = '/login';
    }
  };

  const navItems = [
    { name: 'Agenda', path: '/admin/agenda' },
    { name: 'Esquema', path: '/admin/esquema' },
    { name: 'Alumnos', path: '/admin/alumnos' },
    { name: 'Profesores', path: '/admin/profesores' },
    { name: 'Planes', path: '/admin/planes' },
    { name: 'Clases', path: '/admin/clases' }
  ];

  return (
    <div className="flex min-h-screen bg-background font-sans">
      {/* Sidebar */}
      <aside className="hidden lg:flex w-64 shrink-0 bg-card border-r border-violett-100 flex flex-col sticky top-0 h-screen overflow-y-auto custom-scrollbar">
        <div className="p-6 pb-2">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-violett-900 flex items-center justify-center text-white font-bold italic">V</div>
            <span className="font-bold text-xl text-violett-900 tracking-tight">Violett</span>
          </div>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mt-4">Panel de Negocio</h2>
        </div>
        <nav className="flex-1 mt-4">
          <ul className="flex flex-col gap-1 px-3">
            {navItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path);
              return (
                <li key={item.name}>
                  <Link
                    to={item.path}
                    className={`block py-3 px-4 rounded-xl text-sm transition-all ${
                      isActive 
                        ? 'text-violett-900 font-bold bg-violett-100 shadow-sm' 
                        : 'text-muted hover:bg-violett-50 hover:text-foreground'
                    }`}
                  >
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <div className="p-4 border-t border-violett-100">
          <button 
            onClick={handleLogout}
            className="w-full py-3 px-4 text-sm font-medium text-rose-600 hover:bg-rose-50 rounded-xl transition-colors text-left"
          >
            Cerrar Sesión
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <header className="px-4 lg:px-8 py-4 lg:py-6 flex items-center justify-between lg:justify-end border-b lg:border-none border-violett-100 bg-background sticky top-0 z-10">
          <button 
            onClick={() => setIsMobileMenuOpen(true)}
            className="lg:hidden p-2 text-violett-900 rounded-lg hover:bg-violett-50"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
          <div className="flex items-center gap-3">
             <span className="text-sm font-semibold text-muted">Admin Team</span>
             <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center text-white text-sm font-bold shadow-sm">A</div>
          </div>
        </header>
        <div className="px-8 pb-8 max-w-7xl mx-auto">
          <AnimatePresence mode="wait">
            <motion.div 
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.32, 0.72, 0, 1] } }}
              exit={{ opacity: 0, transition: { duration: 0.15 } }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </div>
      
      <AnimatePresence>
        {isMobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileMenuOpen(false)}
              className="fixed inset-0 bg-black/40 z-40 lg:hidden backdrop-blur-sm"
            />
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', bounce: 0, duration: 0.4 }}
              className="fixed top-0 left-0 bottom-0 w-64 bg-card z-50 flex flex-col border-r border-violett-100 shadow-2xl lg:hidden"
            >
              <div className="p-6 pb-2 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-violett-900 flex items-center justify-center text-white font-bold italic">V</div>
                  <span className="font-bold text-xl text-violett-900 tracking-tight">Violett</span>
                </div>
                <button onClick={() => setIsMobileMenuOpen(false)} className="text-muted hover:text-foreground">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
              <h2 className="px-6 text-sm font-semibold text-muted uppercase tracking-wider mt-2 mb-4">Menú</h2>
              <nav className="flex-1 overflow-y-auto">
                <ul className="flex flex-col gap-1 px-3">
                  {navItems.map((item) => {
                    const isActive = location.pathname.startsWith(item.path);
                    return (
                      <li key={item.name}>
                        <Link
                          to={item.path}
                          className={`block py-3 px-4 rounded-xl text-sm transition-all ${
                            isActive 
                              ? 'text-violett-900 font-bold bg-violett-100 shadow-sm' 
                              : 'text-muted hover:bg-violett-50 hover:text-foreground'
                          }`}
                        >
                          {item.name}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </nav>
              <div className="p-4 border-t border-violett-100">
                <button 
                  onClick={handleLogout}
                  className="w-full py-3 px-4 text-sm font-medium text-rose-600 hover:bg-rose-50 rounded-xl transition-colors text-left"
                >
                  Cerrar Sesión
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    
      </main>
    </div>
  );
}
