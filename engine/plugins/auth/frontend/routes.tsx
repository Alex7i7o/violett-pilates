import React from 'react';
import { RouteObject } from 'react-router-dom';
import { LoginPlugin } from './components/LoginPlugin';
import { ForgotPasswordPlugin } from './components/ForgotPasswordPlugin';
import { ResetPasswordPlugin } from './components/ResetPasswordPlugin';

export const publicRoutes: RouteObject[] = [
  { path: 'login', element: <LoginPlugin /> },
  { path: 'forgot-password', element: <ForgotPasswordPlugin /> },
  { path: 'reset-password/:uidb64/:token', element: <ResetPasswordPlugin /> }
];

export const roleRoutes: Record<string, RouteObject[]> = {};
export const adminRoutes: RouteObject[] = [];
export const adminSidebarItems = [];
export const slots = {};
