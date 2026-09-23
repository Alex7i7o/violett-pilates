# 🧩 Especificación Estándar de Plugins FireSeed (PLUGIN_SPEC)

Esta documentación define el contrato obligatorio que debe cumplir cualquier plugin (Lego) desarrollado para el motor FireSeed, asegurando que pueda conectarse y desconectarse sin afectar el resto de la aplicación.

## 📁 1. Estructura de Directorios

Cada plugin debe residir dentro de engine/plugins/<nombre_del_plugin>/ y debe contener estrictamente dos subdirectorios:
- ackend/ (Aplicación Django)
- rontend/ (Componentes y rutas React)

Ejemplo del plugin Auth:
`	ext
engine/plugins/auth/
├── backend/
│   ├── apps.py           # Configuración (name='plugins.auth.backend')
│   ├── models.py         # Modelos de BD específicos del plugin
│   ├── views.py          # Lógica de la API (Endpoints)
│   ├── urls.py           # Rutas del backend
│   ├── serializers.py    # Serializadores REST
│   └── hooks.py          # Opcional: Para conectarse a eventos globales
└── frontend/
    ├── components/       # Componentes visuales (LoginPlugin.tsx, etc.)
    ├── routes.tsx        # OBLIGATORIO: Contrato de exportación para Vite
    └── hooks/            # Hooks de React internos del plugin
`

## 🔌 2. Contrato Frontend (outes.tsx)

Para que el pluginLoader detecte e integre automáticamente el plugin en el frontend, el archivo rontend/routes.tsx debe exportar SIEMPRE este formato:

`	ypescript
// engine/plugins/auth/frontend/routes.tsx
import React from 'react';
import { RouteObject } from 'react-router-dom';

// 1. Rutas Públicas (Sin estar logueado)
export const publicRoutes: RouteObject[] = [
  { path: 'login', element: <LoginPlugin /> },
  { path: 'forgot-password', element: <ForgotPasswordPlugin /> }
];

// 2. Rutas Privadas del Cliente (App)
export const roleRoutes: Record<string, RouteObject[]> = {
  CLIENTE: [
    { path: 'perfil/seguridad', element: <SecuritySettingsPlugin /> }
  ]
};

// 3. Rutas de Administración (Panel)
export const adminRoutes: RouteObject[] = [];

// 4. Ítems del Menú Lateral (Sidebar)
export const adminSidebarItems = [];

// 5. Componentes Inyectables (PluginSlots)
export const slots = {
  'header-actions': <LogoutButton />
};
`
*Si un plugin no usa alguna de estas propiedades, debe exportarla vacía (ej. export const adminRoutes = [];).*

## ⚙️ 3. Activación mediante client-config.json

El plugin **no existirá** en la aplicación hasta que se agregue explícitamente al array ctive_plugins en la configuración del cliente (ej. config_pilates/client-config.json).

`json
{
  "active_plugins": [
    "auth",
    "membresias",
    "pagos"
  ]
}
`

## 🎯 4. Regla de Oro (Independencia Absoluta)

- **Prohibido importar entre plugins:** Un plugin no puede hacer import { algo } from '../../otro_plugin/'. Si necesitan comunicarse, deben hacerlo a través de eventos, la API del motor base, o la base de datos compartida.
- **Fail-safe:** Si el plugin se desactiva, el resto de la aplicación no debe crashear. Para componentes que se incrustan en la app principal (ej. un widget de pagos), usar SIEMPRE el componente <PluginSlot name="widget-pagos" /> el cual renderizará nada si el plugin está apagado.
