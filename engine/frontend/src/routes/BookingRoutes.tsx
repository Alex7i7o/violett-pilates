import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

import { useClientProfile } from '../hooks/useClientProfile';
import { useClientConfig } from '../context/ClientConfigContext';
import { api } from '../lib/api';




import { Dashboard } from '../pages/Dashboard';
import { ClientLayout } from './ClientLayout';
import { InicioView } from '../pages/client/InicioView';
import { ReservasView } from '../pages/client/ReservasView';
import { PerfilView } from '../pages/client/PerfilView';


import { AdminLayout } from '../layouts/AdminLayout';
import { AgendaAdmin } from '../pages/admin/AgendaAdmin';
import { PlantillasAdmin } from '../pages/admin/PlantillasAdmin';
import { AlumnosAdmin } from '../pages/admin/AlumnosAdmin';
import { ProfesoresAdmin } from '../pages/admin/ProfesoresAdmin';
import { PlanesAdmin } from '../pages/admin/PlanesAdmin';
import { ClasesAdmin } from '../pages/admin/ClasesAdmin';
import { ReglasNegocioAdmin } from '../pages/admin/ReglasNegocioAdmin';

import { getPluginAdminRoutes, getPluginRoleRoute, getPluginPublicRoutes } from '../core/pluginLoader';

export function BookingRoutes() {
  const location = useLocation();
  const config = useClientConfig();
  const { profile, loading, error, refetch } = useClientProfile();

  const handleLogout = async () => {
    const baseUrl = import.meta.env.BASE_URL || '/';
    const loginPath = baseUrl.endsWith('/') ? baseUrl + 'login' : baseUrl + '/login';
    try {
      await api.post('/auth/logout/');
    } catch (err) {
      console.error(err);
    } finally {
      document.body.innerHTML = '';
      window.location.replace(loginPath);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-primary-main font-medium bg-background">
        Cargando...
      </div>
    );
  }

  if (error || !profile) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLoginSuccess={refetch} />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:uidb64/:token" element={<ResetPassword />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  // Rutas exclusivas para el Staff / Admin
  if (profile.rol === 'ADMIN') {
    const adminPluginRoutes = getPluginAdminRoutes(config.active_plugins);
    return (
      <Routes>
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="agenda" replace />} />
          <Route path="reglas" element={<ReglasNegocioAdmin />} />
          <Route path="agenda" element={<AgendaAdmin />} />
          <Route path="esquema" element={<PlantillasAdmin />} />
          <Route path="alumnos" element={<AlumnosAdmin />} />
          <Route path="profesores" element={<ProfesoresAdmin />} />
          <Route path="planes" element={<PlanesAdmin />} />
          <Route path="clases" element={<ClasesAdmin />} />
          
          {/* Plugin Injected Routes */}
          {adminPluginRoutes.map((pr, idx) => (
            <Route key={idx} path={pr.path} element={pr.element} />
          ))}
        </Route>
        {/* Si un admin intenta ir a la ruta de cliente, lo forzamos a volver a su panel */}
        <Route path="*" element={<Navigate to="/admin/agenda" replace />} />
      </Routes>
    );
  }

  // Verificar si hay una ruta exclusiva de rol inyectada por un plugin (Ej: Profesor)
  const pluginRoleRoute = getPluginRoleRoute(profile.rol, config.active_plugins);
  if (pluginRoleRoute) {
    return <>{pluginRoleRoute}</>;
  }

  
  // Rutas exclusivas para Clientes
  return (
    <Routes>
      <Route path="/" element={<ClientLayout />}>
        <Route index element={<InicioView />} />
        <Route path="mis-reservas" element={<ReservasView />} />
        <Route path="perfil" element={<PerfilView />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );

}

