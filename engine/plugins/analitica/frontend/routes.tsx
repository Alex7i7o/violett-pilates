import React from 'react';
import AnalyticsDashboard from './views/AnalyticsDashboard';
import { BarChart3 } from 'lucide-react'; // Wait, icon needs to be rendered? 
// No, adminSidebarItems usually just passes string or maybe an Icon component?
// Let's check other plugins first. I'll just omit icon if it's not supported, but I can put a generic string.

export const adminRoutes = [
  { path: 'analitica', element: <AnalyticsDashboard /> }
];

export const adminSidebarItems = [
  { name: 'Estadísticas', path: '/admin/analitica', icon: 'BarChart3' }
];

export const publicRoutes = [];
