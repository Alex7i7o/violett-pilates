/* Developed by FireSeed - Fueling Innovation */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { FeedbackButton } from '../components/ui/FeedbackButton'
import { api } from '../lib/api'

export function Login({ onLoginSuccess }: { onLoginSuccess: () => void }) {
  const [isAdminMode, setIsAdminMode] = useState(false)
  const [isRegisterMode, setIsRegisterMode] = useState(false)
  
  // Login fields
  const [email, setEmail] = useState('alumno@violett.com')
  const [password, setPassword] = useState('violett123')
  
  // Register additional fields
  const [nombre, setNombre] = useState('')
  const [apellido, setApellido] = useState('')
  const [telefono, setTelefono] = useState('')
  const [contacto, setContacto] = useState('')
  const [notas, setNotas] = useState('')
  const [fechaNacimiento, setFechaNacimiento] = useState('')
  const [sexo, setSexo] = useState('')

  const [error, setError] = useState('')
  const navigate = useNavigate();
  const [status, setStatus] = useState<'idle' | 'loading' | 'success'>('idle')

  const toggleAdminMode = () => {
    setIsRegisterMode(false)
    if (isAdminMode) {
      setIsAdminMode(false)
      setEmail('alumno@violett.com')
      setPassword('violett123')
    } else {
      setIsAdminMode(true)
      setEmail('admin@fireseed.com')
      setPassword('admin123')
    }
  }

  const toggleRegisterMode = () => {
    setIsAdminMode(false)
    setIsRegisterMode(!isRegisterMode)
    setEmail('')
    setPassword('')
    setError('')
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setStatus('loading')

    try {
      await api.post('/auth/login/', { email, password })
      setStatus('success')
      setTimeout(() => onLoginSuccess(), 1000)
    } catch (err: any) {
      setStatus('idle')
      if (err.response?.data?.non_field_errors) {
        setError(err.response.data.non_field_errors[0])
      } else {
        setError('Error de conexión o credenciales inválidas.')
      }
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setStatus('loading')

    try {
      const registerData = {
        email,
        password,
        nombre,
        apellido,
        telefono,
        contacto_emergencia: contacto,
        notas_medicas: notas,
        fecha_nacimiento: fechaNacimiento,
        sexo
      }
      
      await api.post('/auth/registration/', registerData)
      await api.post('/auth/login/', { email, password })
      setStatus('success')
      setTimeout(() => onLoginSuccess(), 1000)
    } catch (err: any) {
      setStatus('idle')
      if (err.response?.data) {
        const errors = err.response.data
        const errorMessages = Object.entries(errors).map(([key, val]) => `${key}: ${val}`).join(' | ')
        setError(errorMessages)
      } else {
        setError('Error al registrar usuario.')
      }
    }
  }

  if (isRegisterMode) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 py-12">
        <Card className="w-full max-w-md shadow-glass">
          <CardHeader className="text-center pb-2">
            <div className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold italic mx-auto mb-4 text-xl bg-violett-900">
              V
            </div>
            <CardTitle className="text-2xl text-violett-900">Crear mi cuenta</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-semibold text-foreground">Nombre</label>
                  <input type="text" required value={nombre} onChange={e=>setNombre(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500" />
                </div>
                <div>
                  <label className="text-sm font-semibold text-foreground">Apellido</label>
                  <input type="text" required value={apellido} onChange={e=>setApellido(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500" />
                </div>
              </div>
              <div>
                <label className="text-sm font-semibold text-foreground">Email</label>
                <input type="email" required value={email} onChange={e=>setEmail(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500" />
              </div>
              <div>
                <label className="text-sm font-semibold text-foreground">Contraseña</label>
                <input type="password" required value={password} onChange={e=>setPassword(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500" minLength={8} placeholder="MÃ­nimo 8 caracteres" />
              </div>
              <div>
                <label className="text-sm font-semibold text-foreground">Teléfono (WhatsApp)</label>
                <input type="text" required value={telefono} onChange={e=>setTelefono(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500" />
              </div>
              <div>
                <label className="text-sm font-semibold text-foreground">Fecha de Nacimiento</label>
                <input type="date" required value={fechaNacimiento} onChange={e=>setFechaNacimiento(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white" />
              </div>

              <div>
                <label className="text-sm font-semibold text-foreground">Contacto de Emergencia</label>
                <input type="text" value={contacto} onChange={e=>setContacto(e.target.value)} placeholder="Ej: Mamá (1145...)" className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500" />
              </div>
              <div>
                <label className="text-sm font-semibold text-foreground">Notas Médicas o Lesiones</label>
                <textarea value={notas} onChange={e=>setNotas(e.target.value)} rows={2} className="w-full p-2.5 rounded-xl border border-violett-200 mt-1 focus:outline-none focus:ring-2 focus:ring-violett-500"></textarea>
              </div>

              {error && <p className="text-red-500 text-sm text-center font-medium">{error}</p>}
              <div className="flex justify-center w-full"><FeedbackButton status={status} type="submit" className="w-full py-6 text-base" initialText="Comenzar en Violett" successText="¡Cuenta creada!" /></div>
            </form>

            <div className="mt-6 text-center border-t border-gray-100 pt-4">
              <button onClick={toggleRegisterMode} className="text-sm text-gray-500 hover:text-violet-700 transition-colors font-medium underline">
                Ya tengo cuenta, iniciar sesión
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-glass">
        <CardHeader className="text-center pb-2">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold italic mx-auto mb-4 text-xl ${isAdminMode ? 'bg-slate-900' : 'bg-violett-900'}`}>
            {isAdminMode ? 'A' : 'V'}
          </div>
          <CardTitle className={`text-2xl ${isAdminMode ? 'text-slate-900' : 'text-violett-900'}`}>
            {isAdminMode ? 'Panel de Negocio' : 'Bienvenida a Violett'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="text-sm font-semibold text-foreground">
                {isAdminMode ? 'Email corporativo' : 'Email de alumna'}
              </label>
              <input 
                type="email" 
                value={email} 
                onChange={e => setEmail(e.target.value)} 
                className={`w-full p-2.5 rounded-xl border mt-1 focus:outline-none focus:ring-2 ${isAdminMode ? 'border-slate-300 focus:ring-slate-500' : 'border-violett-200 focus:ring-violett-500'}`} 
                required
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-foreground">Contraseña</label>
              <input 
                type="password" 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                className={`w-full p-2.5 rounded-xl border mt-1 focus:outline-none focus:ring-2 ${isAdminMode ? 'border-slate-300 focus:ring-slate-500' : 'border-violett-200 focus:ring-violett-500'}`} 
                required
              />
            </div>
            {!isAdminMode && !isRegisterMode && (
              <div className="flex justify-end mt-2">
                <button type="button" onClick={() => navigate('/forgot-password')} className="text-sm text-violett-600 hover:text-violett-800 transition-colors font-medium">¿Olvidaste tu contraseña?</button>
              </div>
            )}
            {error && <p className="text-red-500 text-sm text-center font-medium">{error}</p>}
            <div className="flex justify-center w-full"><FeedbackButton status={status} type="submit" className={`w-full py-6 text-base ${isAdminMode ? 'bg-slate-900 hover:bg-slate-800 text-white' : ''}`} initialText="Ingresar" successText="¡Bienvenido!" /></div>
          </form>

          {!isAdminMode && (
            <div className="mt-4 text-center">
              <button 
                type="button"
                onClick={toggleRegisterMode}
                className="text-sm text-violett-700 hover:text-violett-900 font-bold underline transition-colors"
              >
                Registrarme
              </button>
            </div>
          )}

          <div className="mt-6 text-center border-t border-gray-100 pt-4">
            <button 
              type="button"
              onClick={toggleAdminMode}
              className="text-sm text-gray-500 hover:text-violet-700 transition-colors font-medium underline"
            >
              {isAdminMode ? 'Volver a acceso de alumnas' : 'Acceso Staff / Panel de Negocio'}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


