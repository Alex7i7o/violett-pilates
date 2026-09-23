import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { api } from '../lib/api';
import { Eye, EyeOff } from 'lucide-react';

export function ResetPassword() {
  const navigate = useNavigate();
  const { uidb64: uid, token } = useParams();
  
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  if (!uid || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-6 text-center">
            <p className="text-red-500 mb-4">El enlace es inválido o ha expirado.</p>
            <button onClick={() => navigate('/')} className="text-violett-600 underline">Volver al inicio</button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== passwordConfirm) {
      setErrorMsg('Las contraseñas no coinciden.');
      return;
    }
    
    setStatus('loading');
    setErrorMsg('');
    
    try {
      await api.post('/auth/password/reset/confirm/', {
        uid,
        token,
        new_password1: password,
        new_password2: passwordConfirm
      });
      setStatus('success');
    } catch (err: any) {
      setStatus('error');
      setErrorMsg('El enlace ha expirado o es inválido. Por favor, solicitá uno nuevo.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <Card className="w-full max-w-md shadow-glass">
        <CardHeader className="text-center pb-2">
          <CardTitle className="text-2xl text-primary-main">Elige tu nueva contraseña</CardTitle>
        </CardHeader>
        <CardContent>
          {status === 'success' ? (
            <div className="text-center space-y-4">
              <p className="text-green-600 font-medium">¡Tu contraseña ha sido actualizada con éxito!</p>
              <button onClick={() => navigate('/')} className="w-full bg-primary-main hover:bg-primary-hover text-white p-3 rounded-xl font-bold transition-all">
                Ir a Iniciar Sesión
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-semibold text-foreground">Nueva contraseña</label>
                <div className="relative mt-1">
                  <input 
                    type={showPassword ? "text" : "password"} 
                    required 
                    minLength={8}
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                    className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" 
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-semibold text-foreground">Confirmar nueva contraseña</label>
                <input 
                  type={showPassword ? "text" : "password"} 
                  required 
                  minLength={8}
                  value={passwordConfirm} 
                  onChange={e => setPasswordConfirm(e.target.value)} 
                  className="w-full p-2.5 rounded-xl border border-primary-light mt-1 focus:outline-none focus:ring-2 focus:ring-primary-main" 
                />
              </div>

              {errorMsg && <p className="text-red-500 text-sm text-center">{errorMsg}</p>}
              
              <button type="submit" disabled={status === 'loading'} className="w-full bg-primary-main hover:bg-primary-hover text-white p-3 rounded-xl font-bold transition-all disabled:opacity-50">
                {status === 'loading' ? 'Guardando...' : 'Guardar contraseña'}
              </button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
