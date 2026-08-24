import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

export function ProfesorLayout() {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/');
      window.location.href = '/';
    } catch (e) {
      window.location.href = '/';
    }
  };

  return (
    <div className="flex min-h-screen bg-background font-sans">
      <main className="flex-1 overflow-auto flex flex-col">
        <header className="bg-card shadow-sm border-b border-violett-100 sticky top-0 z-40">
          <div className="max-w-6xl mx-auto px-4 sm:px-8 h-16 flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-violett-900 flex items-center justify-center text-white font-bold italic">V</div>
              <span className="font-bold text-xl text-violett-900 tracking-tight">Violett<span className="text-violett-400">Staff</span></span>
            </div>
            <nav className="flex items-center gap-4">
              <button onClick={handleLogout} className="text-sm font-medium text-rose-600 hover:text-rose-700 transition-colors">
                Cerrar Sesión
              </button>
            </nav>
          </div>
        </header>
        
        <div className="p-4 sm:p-8 max-w-6xl mx-auto w-full flex-1">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
