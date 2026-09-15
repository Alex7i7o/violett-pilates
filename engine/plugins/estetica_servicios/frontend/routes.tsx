import React, { lazy, Suspense } from 'react';

const ServiciosAdmin = lazy(() => import('./ServiciosAdmin').then(m => ({ default: m.ServiciosAdmin })));

export const adminRoutes = [
  { 
    path: 'servicios', 
    element: (
      <Suspense fallback={<div className="p-4">Cargando Servicios...</div>}>
        <ServiciosAdmin />
      </Suspense>
    )
  }
];

export const adminSidebarItems = [
  { name: 'Servicios', path: '/admin/servicios' }
];
