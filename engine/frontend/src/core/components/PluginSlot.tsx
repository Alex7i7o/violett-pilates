import React, { Suspense } from 'react';
import { useClientConfig } from '../../context/ClientConfigContext';

interface PluginSlotProps {
  name: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PluginSlot({ name, children, fallback = null }: PluginSlotProps) {
  const { active_plugins } = useClientConfig() as any;

  // Si active_plugins no existe o el plugin no está en la lista, no montamos nada.
  if (!active_plugins || !active_plugins.includes(name)) {
    return <>{fallback}</>;
  }

  return (
    <Suspense fallback={<div className="animate-pulse bg-gray-200 h-10 w-full rounded"></div>}>
      {children}
    </Suspense>
  );
}
