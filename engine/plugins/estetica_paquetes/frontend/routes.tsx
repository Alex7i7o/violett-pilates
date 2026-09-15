import React, { lazy, Suspense } from 'react';

const ReglasAdmin = lazy(() => import('./ReglasAdmin').then(m => ({ default: m.ReglasAdmin })));

export const adminRoutes = [
  { 
    path: 'paquetes', 
    element: (
      <Suspense fallback={<div className="p-4">Cargando Configuración...</div>}>
        <ReglasAdmin />
      </Suspense>
    )
  }
];

export const adminSidebarItems = [
  { name: 'Paquetes', path: '/admin/paquetes' }
];
