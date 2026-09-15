import React, { lazy, Suspense } from 'react';

const ResenasAdmin = lazy(() => import('./ResenasAdmin').then(m => ({ default: m.ResenasAdmin })));

export const adminRoutes = [
  { 
    path: 'resenas', 
    element: (
      <Suspense fallback={<div className="p-4">Cargando Reseñas...</div>}>
        <ResenasAdmin />
      </Suspense>
    )
  }
];

export const adminSidebarItems = [
  { name: 'Reseñas', path: '/admin/resenas' }
];
