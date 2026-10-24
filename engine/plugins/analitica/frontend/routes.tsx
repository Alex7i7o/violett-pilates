import React from 'react';
import AnalyticsDashboard from './views/AnalyticsDashboard';
import { BarChart3 } from 'lucide-react';

export const adminRoutes = [
  { path: 'analitica', element: <AnalyticsDashboard /> }
];

export const adminSidebarItems = [
  { name: 'Estadísticas', path: '/admin/analitica', icon: BarChart3 }
];

export const publicRoutes = [];
