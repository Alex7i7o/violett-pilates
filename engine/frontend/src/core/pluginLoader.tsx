import React, { Suspense } from 'react';

// Load all routes.tsx from all plugins eagerly
const modules = import.meta.glob('@plugins/*/frontend/routes.tsx', { eager: true });

export interface PluginRoute {
  path: string;
  element: React.ReactNode;
}

export interface PluginSidebarItem {
  name: string;
  path: string;
}

export const getPluginAdminRoutes = (): PluginRoute[] => {
  const routes: PluginRoute[] = [];
  for (const path in modules) {
    const mod = modules[path] as any;
    if (mod && mod.adminRoutes) {
      routes.push(...mod.adminRoutes);
    }
  }
  return routes;
};

export const getPluginAdminSidebarItems = (): PluginSidebarItem[] => {
  const items: PluginSidebarItem[] = [];
  for (const path in modules) {
    const mod = modules[path] as any;
    if (mod && mod.adminSidebarItems) {
      items.push(...mod.adminSidebarItems);
    }
  }
  return items;
};

export const getPluginRoleRoute = (role: string): React.ReactNode | null => {
  for (const path in modules) {
    const mod = modules[path] as any;
    if (mod && mod.roleRoutes && mod.roleRoutes[role]) {
      return mod.roleRoutes[role];
    }
  }
  return null;
};
