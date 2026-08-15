/* Developed by FireSeed - Fueling Innovation */
import React from 'react'
import { Dashboard } from './pages/Dashboard'
import { Login } from './pages/Login'
import { useClientProfile } from './hooks/useClientProfile'
import { api } from './lib/api'

function App() {
  const { profile, loading, error, refetch } = useClientProfile()

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/')
      refetch() // Will fail and show login
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Navbar Simple */}
      <header className="bg-card shadow-sm border-b border-violett-100 sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-violett-900 flex items-center justify-center text-white font-bold italic">V</div>
            <span className="font-bold text-xl text-violett-900 tracking-tight">Violett<span className="text-violett-400">Pilates</span></span>
          </div>
          <nav className="flex gap-4">
            {profile && (
              <button onClick={handleLogout} className="text-sm font-medium text-muted hover:text-foreground transition-colors">
                Cerrar Sesión
              </button>
            )}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full p-4 md:p-8">
        {loading ? (
          <div className="min-h-[60vh] flex items-center justify-center text-violett-900 font-medium">Cargando...</div>
        ) : error || !profile ? (
          <Login onLoginSuccess={refetch} />
        ) : (
          <Dashboard />
        )}
      </main>

      {/* Footer con Firma FireSeed */}
      <footer className="py-8 mt-12 bg-white border-t border-violett-100 text-center">
        <p className="text-xs font-medium text-muted/60 uppercase tracking-widest">
          Powered by <span className="text-violett-700 font-bold">FireSeed</span>
        </p>
      </footer>
    </div>
  )
}

export default App
