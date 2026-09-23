import React from 'react';
import { RouteObject } from 'react-router-dom';
import { Login as LoginPlugin } from './components/LoginPlugin';
import { ForgotPassword as ForgotPasswordPlugin } from './components/ForgotPasswordPlugin';
import { ResetPassword as ResetPasswordPlugin } from './components/ResetPasswordPlugin';

export const publicRoutes: RouteObject[] = [
  { path: '/login', element: <LoginPlugin /> },
  { path: 'login', element: <LoginPlugin /> },
  { path: '/forgot-password', element: <ForgotPasswordPlugin /> },
  { path: 'forgot-password', element: <ForgotPasswordPlugin /> },
  { path: '/reset-password/:uidb64/:token', element: <ResetPasswordPlugin /> },
  { path: 'reset-password/:uidb64/:token', element: <ResetPasswordPlugin /> }
];

export const roleRoutes: Record<string, RouteObject[]> = {};
export const adminRoutes: RouteObject[] = [];
export const adminSidebarItems = [];
export const slots = {};
