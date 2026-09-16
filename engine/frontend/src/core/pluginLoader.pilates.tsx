/* Developed by FireSeed - Fueling Innovation */
/**
 * Plugin Loader — PILATES BUILD
 * Only loads plugins that belong to the Pilates instance.
 * Estetica plugins are physically excluded from this bundle.
 */
import React from 'react';

const modules = import.meta.glob([
  '@plugins/profesores/frontend/routes.tsx',
  '@plugins/resenas/frontend/routes.tsx',
], { eager: true });

export interface PluginRoute {
  path: string;
  element: React.ReactNode;
}

export interface PluginSidebarItem {
  name: string;
  path: string;
}

const getPluginNameFromPath = (path: string): string => {
  const match = path.match(/@plugins\/([^/]+)\//);
  return match ? match[1] : '';
};

export const getPluginAdminRoutes = (activePlugins: string[]): PluginRoute[] => {
  const routes: PluginRoute[] = [];
  for (const path in modules) {
    const pluginName = getPluginNameFromPath(path);
    if (!activePlugins.includes(pluginName)) continue;
    const mod = modules[path] as any;
    if (mod && mod.adminRoutes) routes.push(...mod.adminRoutes);
  }
  return routes;
};

export const getPluginAdminSidebarItems = (activePlugins: string[]): PluginSidebarItem[] => {
  const items: PluginSidebarItem[] = [];
  for (const path in modules) {
    const pluginName = getPluginNameFromPath(path);
    if (!activePlugins.includes(pluginName)) continue;
    const mod = modules[path] as any;
    if (mod && mod.adminSidebarItems) items.push(...mod.adminSidebarItems);
  }
  return items;
};

export const getPluginRoleRoute = (role: string, activePlugins: string[]): React.ReactNode | null => {
  for (const path in modules) {
    const pluginName = getPluginNameFromPath(path);
    if (!activePlugins.includes(pluginName)) continue;
    const mod = modules[path] as any;
    if (mod && mod.roleRoutes && mod.roleRoutes[role]) return mod.roleRoutes[role];
  }
  return null;
};
