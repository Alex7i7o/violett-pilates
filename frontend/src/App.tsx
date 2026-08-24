/* Developed by FireSeed - Fueling Innovation */
import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { Login } from './pages/Login'
import { useClientProfile } from './hooks/useClientProfile'
import { api } from './lib/api'

import { AdminLayout } from './layouts/AdminLayout'
import { AgendaAdmin } from './pages/admin/AgendaAdmin'
import { AlumnosAdmin } from './pages/admin/AlumnosAdmin'
import { ProfesoresAdmin } from './pages/admin/ProfesoresAdmin'
import { PlanesAdmin } from './pages/admin/PlanesAdmin'

import { ProfesorLayout } from './layouts/ProfesorLayout'
import { ProfesorDashboard } from './pages/profesor/ProfesorDashboard'

function AppRoutes() {
  const { profile, loading, error, refetch } = useClientProfile()

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/')
      refetch() // Will fail and show login
    } catch (err) {
      console.error(err)
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-violet-900 font-medium bg-background">Cargando...</div>
  }

  if (error || !profile) {
    return <Login onLoginSuccess={refetch} />
  }

  // Rutas exclusivas para el Staff / Admin
  if (profile.rol === 'ADMIN') {
    return (
      <Routes>
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="agenda" replace />} />
          <Route path="agenda" element={<AgendaAdmin />} />
          <Route path="alumnos" element={<AlumnosAdmin />} />
          <Route path="profesores" element={<ProfesoresAdmin />} />
          <Route path="planes" element={<PlanesAdmin />} />
        </Route>
        {/* Si un admin intenta ir a la ruta de cliente, lo forzamos a volver a su panel */}
        <Route path="*" element={<Navigate to="/admin/agenda" replace />} />
      </Routes>
    )
  }

  // Rutas exclusivas para Profesores
  if (profile.rol === 'PROFESOR') {
    return (
      <Routes>
        <Route path="/profesor" element={<ProfesorLayout />}>
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<ProfesorDashboard />} />
        </Route>
        <Route path="*" element={<Navigate to="/profesor/dashboard" replace />} />
      </Routes>
    )
  }

  // Rutas exclusivas para Clientes
  return (
    <Routes>
      <Route path="/" element={
        <div className="min-h-screen flex flex-col bg-background">
          <header className="bg-card shadow-sm border-b border-violet-100 sticky top-0 z-40">
            <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-violet-900 flex items-center justify-center text-white font-bold italic">V</div>
                <span className="font-bold text-xl text-violet-900 tracking-tight">Violett<span className="text-violet-400">Pilates</span></span>
              </div>
              <nav className="flex gap-4">
                <button onClick={handleLogout} className="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors ml-4">
                  Cerrar Sesión
                </button>
              </nav>
            </div>
          </header>
          <main className="flex-1 w-full p-4 md:p-8">
            <Dashboard />
          </main>
          <footer className="py-8 mt-12 bg-white border-t border-violet-100 text-center">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-widest">
              Powered by <span className="text-violet-700 font-bold">FireSeed</span>
            </p>
          </footer>
        </div>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

export default App
