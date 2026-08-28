import React, { useState } from 'react';
import { Card, CardContent } from '../components/ui/Card';
import { InputField } from '../components/ui/InputField';
import { FeedbackButton } from '../components/ui/FeedbackButton';
import { api } from '../lib/api';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

export function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    
    // Sanitization: trim spaces
    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setStatus('error');
      return;
    }

    try {
      await api.post('/auth/password/reset/', { email: cleanEmail });
      setStatus('success');
    } catch (e) {
      // Don't leak whether the email exists or not
      setStatus('success');
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
          
          <h2 className="text-2xl font-bold text-center text-slate-900 mb-2">Recuperar Contraseña</h2>
          
          {status === 'success' ? (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="text-center space-y-4">
              <p className="text-slate-600">Si el correo está registrado, te enviamos un enlace para restablecer tu contraseña.</p>
              <button onClick={() => navigate('/login')} className="text-violett-700 font-bold underline">Volver al inicio de sesión</button>
            </motion.div>
          ) : (
            <>
              <p className="text-center text-slate-500 text-sm mb-6">Ingresa tu correo electrónico y te enviaremos instrucciones.</p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <InputField 
                  label="Correo electrónico" 
                  name="email" 
                  type="email" 
                  value={email} 
                  onChange={e => setEmail(e.target.value)} 
                  required 
                />
                <FeedbackButton 
                  status={status} 
                  type="submit" 
                  className="w-full py-4 text-base" 
                  initialText="Enviar enlace" 
                  successText="Enviado" 
                />
              </form>
              <div className="mt-6 text-center">
                <button onClick={() => navigate('/login')} className="text-sm text-slate-500 hover:text-violett-700 underline">Volver atrás</button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
