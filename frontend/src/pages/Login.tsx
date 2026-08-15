/* Developed by FireSeed - Fueling Innovation */
import React, { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { api } from '../lib/api'

export function Login({ onLoginSuccess }: { onLoginSuccess: () => void }) {
  const [email, setEmail] = useState('alumno@violett.com')
  const [password, setPassword] = useState('violett123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/auth/login/', { email, password })
      onLoginSuccess()
    } catch (err: any) {
      setError('Credenciales inválidas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-glass">
        <CardHeader className="text-center pb-2">
          <div className="w-12 h-12 rounded-full bg-violett-900 flex items-center justify-center text-white font-bold italic mx-auto mb-4 text-xl">V</div>
          <CardTitle className="text-2xl text-violett-900">Bienvenida a Violett</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="text-sm font-semibold text-foreground">Email de alumna</label>
              <input 
                type="email" 
                value={email} 
                onChange={e => setEmail(e.target.value)} 
                className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500" 
                required
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-foreground">Contraseña</label>
              <input 
                type="password" 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500" 
                required
              />
            </div>
            {error && <p className="text-red-500 text-sm text-center font-medium">{error}</p>}
            <Button type="submit" className="w-full py-6 text-base" disabled={loading}>
              {loading ? 'Iniciando sesión...' : 'Ingresar a mi cuenta'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
