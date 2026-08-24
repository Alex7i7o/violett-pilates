import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { api } from '../lib/api';

export function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();

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
    { name: 'Planes', path: '/admin/planes' }
  ];

  return (
    <div className="flex min-h-screen bg-background font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-card border-r border-violett-100 flex flex-col">
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
        <header className="px-8 py-6 flex items-center justify-end">
          <div className="flex items-center gap-3">
             <span className="text-sm font-semibold text-muted">Admin Team</span>
             <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center text-white text-sm font-bold shadow-sm">A</div>
          </div>
        </header>
        <div className="px-8 pb-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
