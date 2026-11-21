import React from 'react';
import { EsteticaClientApp } from './EsteticaClientApp';
import { EsteticaAdminHorarios } from './views/EsteticaAdminHorarios';
import { EsteticaAgendaAdmin } from './views/EsteticaAgendaAdmin';

export const roleRoutes = {
  CLIENTE: <EsteticaClientApp />
};

export const adminRoutes = [
  {
    path: 'agenda',
    element: <EsteticaAgendaAdmin />
  },
  {
    path: 'estetica/horarios',
    element: <EsteticaAdminHorarios />
  }
];

export const adminSidebarItems = [
  {
    name: 'Horarios Estética',
    path: '/admin/estetica/horarios'
  }
];
