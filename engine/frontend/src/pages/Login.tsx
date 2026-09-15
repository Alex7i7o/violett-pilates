import { toast } from 'sonner';
import { useClientConfig } from '../context/ClientConfigContext';
import { Eye, EyeOff } from 'lucide-react';
/* Developed by FireSeed - Fueling Innovation */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { useInstallPrompt } from '../hooks/useInstallPrompt';
import { FeedbackButton } from '../components/ui/FeedbackButton'
import { api } from '../lib/api'

export function Login({ onLoginSuccess }: { onLoginSuccess: () => void }) {
  const config = useClientConfig();
  const isEstética = config.client_id === 'violett_estetica';
  const [isAdminMode, setIsAdminMode] = useState(false)
  const [isRegisterMode, setIsRegisterMode] = useState(false)
  
  // Login fields
  const [email, setEmail] = useState('alumno@violett.com')
  const [password, setPassword] = useState('password123')
  
  const [showPassword, setShowPassword] = useState(false);
  
  // Install Prompt Hook
  const { deferredPrompt, isIOS, isStandalone, promptInstall } = useInstallPrompt();
  const [showInstallBanner, setShowInstallBanner] = useState(false);

  useEffect(() => {
    if (!isStandalone && (deferredPrompt || isIOS)) {
      setShowInstallBanner(true);
    }
  }, [isStandalone, deferredPrompt, isIOS]);

  
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
      setPassword('password123')
    } else {
      setIsAdminMode(true)
      setEmail('admin@violett.com')
      setPassword('password123')
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
        let msg = err.response.data.non_field_errors[0]; if (msg === "Unable to log in with provided credentials.") { msg = "El correo o la contraseña son incorrectos."; } setError(msg);
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
                password1: password,
        password2: password,
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
        if (errors.email) {
          setError('El correo ingresado ya está registrado o es inválido.');
        } else {
          const errorMessages = Object.entries(errors).map(([key, val]) => `${key}: ${val}`).join(' | ')
          setError(errorMessages)
        }
      } else {
        setError('Error al registrar usuario.')
      }
    }
  }

  if (isRegisterMode) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 py-12">
        <Card className="w-full max-w-md shadow-glass max-h-[95dvh] overflow-y-auto hide-scrollbar">
          <CardHeader className="text-center pb-2">
            <img src={isEstética ? "/logo-estetica-icon.png" : "/logo-icon.png"} alt="Violett" className="h-20 sm:h-24 mx-auto mb-2 object-contain drop-shadow-md" />
            <CardTitle className="text-2xl text-primary-main">Crear mi cuenta</CardTitle>
          </CardHeader>
          <CardContent>
            <form 
      onInvalid={(e) => {
        e.preventDefault();
        const t = typeof toast !== 'undefined' ? toast : (window as any).toast;
        if(t) t.error('Por favor, completa todos los campos requeridos.');
      }}
      onSubmit={handleRegister} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-semibold text-foreground">Nombre</label>
                  <input type="text" required maxLength={50} value={nombre} onChange={e=>setNombre(e.target.value)} className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main" />
                </div>
                <div>
                  <label className="text-sm font-semibold text-foreground">Apellido</label>
                  <input type="text" required maxLength={50} value={apellido} onChange={e=>setApellido(e.target.value)} className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main" />
                </div>
              </div>
              <div>
                <label className="text-sm font-semibold text-foreground">Email</label>
                <input type="email" required value={email} onChange={e=>setEmail(e.target.value.toLowerCase())} maxLength={50} className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main" />
              </div>
              <div>
                <label className="text-sm font-semibold text-foreground">Contraseña</label>
                <div className="relative mt-1">
                  <input type={showPassword ? "text" : "password"} required value={password} onChange={e=>setPassword(e.target.value)} minLength={8} placeholder="Mínimo 8 caracteres" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none">
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>
              <div>
                <label className="text-sm font-semibold text-foreground">Teléfono (WhatsApp)</label>
                <input type="text" required maxLength={30} value={telefono} onChange={e=>setTelefono(e.target.value)} className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-semibold text-foreground">Fecha de Nacimiento</label>
                  <input type="date" required value={fechaNacimiento} onChange={e=>setFechaNacimiento(e.target.value)} className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main bg-white" />
                </div>
                <div>
                  <label className="text-sm font-semibold text-foreground">Sexo</label>
                  <select required value={sexo} onChange={e=>setSexo(e.target.value)} className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main bg-white">
                    <option value="">Seleccionar...</option>
                    <option value="F">Femenino</option>
                    <option value="M">Masculino</option>
                    <option value="O">Otro</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-sm font-semibold text-foreground">Contacto de Emergencia</label>
                <input type="text" maxLength={50} value={contacto} onChange={e=>setContacto(e.target.value)} placeholder="Ej: Mamá (1145...)" className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main" />
              </div>
              <div>
                <label className="text-sm font-semibold text-foreground">Notas Médicas o Lesiones</label>
                <textarea maxLength={300} value={notas} onChange={e=>setNotas(e.target.value)} rows={2} className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main"></textarea>
              </div>

              {error && <p className="text-red-500 text-sm text-center font-medium">{error}</p>}
              <div className="flex justify-center w-full"><FeedbackButton status={status} type="submit" className="w-full py-6 text-base" initialText="Comenzar en Violett Pilates" successText="¡Bienvenido!" /></div>
          </form>

          

          {!isAdminMode && (
            <div className="mt-4 text-center">
              <button 
                type="button"
                onClick={toggleRegisterMode}
                className="text-sm text-violett-700 hover:text-primary-main font-bold underline transition-colors"
              >
                Registrarme
              </button>
            </div>
          )}

          <div className="mt-6 text-center border-t border-gray-100 pt-4">
            <button 
              type="button"
              onClick={toggleAdminMode}
              className="text-sm text-gray-500 hover:text-primary-hover transition-colors font-medium underline"
            >
              {isAdminMode ? 'Volver a acceso de alumnas' : 'Acceso Staff / Panel de Negocio'}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
  }

  return (
    
      <div className="min-h-screen flex items-center justify-center p-4 py-12">
        {showInstallBanner && (
          <div className="fixed top-0 left-0 right-0 bg-primary-main text-white p-4 shadow-lg z-50 flex items-center justify-between">
            <div>
              <p className="font-bold text-sm">¡Instalá la App!</p>
              <p className="text-xs opacity-90">{isIOS ? "Tocá compartir y luego 'Agregar a Inicio'" : "Para una experiencia más rápida."}</p>
            </div>
            {!isIOS && (
              <button onClick={promptInstall} className="bg-white text-primary-main px-4 py-2 rounded-lg text-sm font-bold shadow-sm">
                Instalar
              </button>
            )}
            <button onClick={() => setShowInstallBanner(false)} className="ml-3 text-white/70 hover:text-white">
               ✕
            </button>
          </div>
        )}
        <Card className="w-full max-w-md shadow-glass">
        <CardHeader className="text-center pb-2">
          <img src={isEstética ? "/logo-estetica-icon.png" : "/logo-icon.png"} alt="Violett" className="h-20 sm:h-24 mx-auto mb-2 object-contain drop-shadow-md" />
          <CardTitle className="text-2xl text-primary-main">{config?.copywriting?.hero_title || 'Bienvenido'}</CardTitle>
          <p className="text-muted text-sm">{config?.copywriting?.hero_subtitle}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-sm font-semibold text-foreground">
                {isAdminMode ? 'Email corporativo' : (isEstética ? 'Email' : 'Email de alumna')}
              </label>
              <input type="email" required value={email} onChange={e=>setEmail(e.target.value.toLowerCase())} maxLength={50} className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main" />
            </div>
            <div>
              <label className="text-sm font-semibold text-foreground">Contraseña</label>
              <div className="relative mt-1">
                <input type={showPassword ? "text" : "password"} required value={password} onChange={e=>setPassword(e.target.value)} minLength={8} />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none">
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            {error && <p className="text-red-500 text-sm text-center font-medium">{error}</p>}
            <div className="flex justify-center w-full">
              <FeedbackButton status={status} type="submit" className={`w-full py-6 text-base ${isAdminMode ? 'bg-slate-900 hover:bg-slate-800 text-white' : ''}`} initialText="Ingresar" successText="¡Bienvenido!" />
            </div>
          </form>

          {!isAdminMode && (
            <div className="mt-4 text-center">
              <button type="button" onClick={toggleRegisterMode} className="text-sm text-violett-700 hover:text-primary-main font-bold underline transition-colors">
                Registrarme
              </button>
            </div>
          )}

          <div className="mt-6 text-center border-t border-gray-100 pt-4">
            <button type="button" onClick={toggleAdminMode} className="text-sm text-gray-500 hover:text-primary-hover transition-colors font-medium underline">
              {isAdminMode ? 'Volver a acceso de alumnas' : 'Acceso Staff / Panel de Negocio'}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
