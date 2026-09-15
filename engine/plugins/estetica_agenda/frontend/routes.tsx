import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { EsteticaClientApp } from './EsteticaClientApp';
import { EsteticaAdminHorarios } from './views/EsteticaAdminHorarios';

export const roleRoutes = {
  CLIENTE: <EsteticaClientApp />
};

export const adminRoutes = [
  {
    path: 'estetica/horarios',
    element: <EsteticaAdminHorarios />
  }
];

export const adminSidebarItems = [
  {
    name: 'Horarios Estética',
    path: 'estetica/horarios'
  }
];
