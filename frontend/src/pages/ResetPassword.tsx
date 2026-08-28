import React, { useState } from 'react';
import { Card, CardContent } from '../components/ui/Card';
import { InputField } from '../components/ui/InputField';
import { FeedbackButton } from '../components/ui/FeedbackButton';
import { api } from '../lib/api';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';

export function ResetPassword() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const navigate = useNavigate();
  const { uid, token } = useParams<{uid: string, token: string}>();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      toast.error('La contraseña debe tener al menos 8 caracteres');
      return;
    }
    if (password !== confirmPassword) {
      toast.error('Las contraseñas no coinciden');
      return;
    }
    
    setStatus('loading');
    
    try {
      await api.post('/auth/password/reset/confirm/', { 
        uid, 
        token, 
        new_password: password, 
        new_password1: confirmPassword 
      });
      setStatus('success');
      toast.success('Contraseña actualizada correctamente');
      setTimeout(() => navigate('/login'), 2000);
    } catch (e) {
      setStatus('error');
      toast.error('El enlace es inválido o ha expirado');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl shadow-violett-900/5">
        <CardContent className="p-8">
          <div className="flex justify-center mb-8">
            <div className="w-12 h-12 rounded-2xl bg-violett-900 flex items-center justify-center">
              <span className="text-2xl font-bold text-white">V</span>
            </div>
          </div>
          
          <h2 className="text-2xl font-bold text-center text-slate-900 mb-6">Crear nueva contraseña</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <InputField 
              label="Nueva contraseña (mínimo 8 caracteres)" 
              name="password" 
              type="password" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              required 
            />
            <InputField 
              label="Confirmar contraseña" 
              name="confirmPassword" 
              type="password" 
              value={confirmPassword} 
              onChange={e => setConfirmPassword(e.target.value)} 
              required 
            />
            <FeedbackButton 
              status={status === 'error' ? 'idle' : status} 
              type="submit" 
              className="w-full py-4 text-base mt-2" 
              initialText="Guardar contraseña" 
              successText="¡Actualizada!" 
            />
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
