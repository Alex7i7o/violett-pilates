import React, { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

const ProfesorLayout = lazy(() => import('./ProfesorLayout').then(m => ({ default: m.ProfesorLayout })));
const ProfesorDashboard = lazy(() => import('./ProfesorDashboard').then(m => ({ default: m.ProfesorDashboard })));

export const roleRoutes = {
  'PROFESOR': (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Cargando Panel Profesor...</div>}>
      <Routes>
        <Route path="/profesor" element={<ProfesorLayout />}>
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<ProfesorDashboard />} />
        </Route>
        <Route path="*" element={<Navigate to="/profesor/dashboard" replace />} />
      </Routes>
    </Suspense>
  )
};
