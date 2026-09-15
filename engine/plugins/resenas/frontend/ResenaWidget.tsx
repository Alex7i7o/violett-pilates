import React, { useState } from 'react';
import { Card, CardContent } from '../../../frontend/src/components/ui/Card';
import { Button } from '../../../frontend/src/components/ui/Button';
import { api } from '../../../frontend/src/lib/api';
import { toast } from 'sonner';

export function ResenaWidget() {
  const [estrellas, setEstrellas] = useState(0);
  const [mensaje, setMensaje] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (estrellas === 0) {
      toast.error('Por favor, selecciona una calificación en estrellas.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/resenas/', { estrellas, mensaje });
      setSubmitted(true);
      toast.success('¡Gracias por tu opinión!');
    } catch (e) {
      toast.error('Ocurrió un error al enviar tu opinión.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <Card className="mt-8 border-emerald-100 bg-emerald-50">
        <CardContent className="p-6 text-center">
          <p className="text-emerald-700 font-medium">¡Gracias por dejarnos tu opinión!</p>
          <p className="text-sm text-emerald-600 mt-1">Tus comentarios nos ayudan a mejorar cada día.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-8 border-primary-light">
      <CardContent className="p-6">
        <h3 className="text-lg font-bold text-primary-main mb-4">¿Qué te pareció tu última clase?</h3>
        
        <div className="flex gap-2 mb-4">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => setEstrellas(star)}
              className={`text-3xl transition-transform hover:scale-110 ${star <= estrellas ? 'text-yellow-400' : 'text-gray-200'}`}
            >
              ★
            </button>
          ))}
        </div>

        <textarea
          value={mensaje}
          onChange={(e) => setMensaje(e.target.value)}
          placeholder="Déjanos un comentario (opcional)..."
          className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-main focus:border-transparent mb-4"
          rows={3}
        />

        <Button 
          onClick={handleSubmit} 
          disabled={loading || estrellas === 0}
          className="w-full sm:w-auto"
        >
          {loading ? 'Enviando...' : 'Enviar Opinión'}
        </Button>
      </CardContent>
    </Card>
  );
}
