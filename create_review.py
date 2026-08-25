# -*- coding: utf-8 -*-
code = """import React, { useState } from 'react';
import { Card, CardContent } from './Card';
import { Button } from './Button';
import { motion } from 'framer-motion';
import { api } from '../../lib/api';
import { toast } from 'sonner';

export function ReviewForm() {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) {
      toast.error('Por favor, selecciona una calificación en estrellas.');
      return;
    }
    setIsSubmitting(true);
    try {
      await api.post('/resenas/', { puntuacion: rating, comentario: comment });
      toast.success('¡Gracias por dejarnos tu reseña!');
      setSubmitted(true);
    } catch (e) {
      toast.error('Error al enviar la reseña.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <Card className="bg-violett-50/50 border-violett-100 mt-12 mb-8">
        <CardContent className="p-8 text-center">
          <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="flex justify-center mb-4 text-4xl">
            🎉
          </motion.div>
          <h3 className="text-xl font-bold text-violett-900 mb-2">¡Muchísimas gracias!</h3>
          <p className="text-muted text-sm">Tu opinión nos ayuda a seguir mejorando para darte el mejor servicio.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-12 mb-8 overflow-hidden border-violett-100 shadow-soft relative">
      {/* Decorative gradient */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violett-400 to-fuchsia-400"></div>
      
      <CardContent className="p-6 md:p-8">
        <div className="md:flex gap-8 items-start">
          <div className="md:w-1/3 mb-6 md:mb-0">
            <h3 className="text-2xl font-bold text-foreground mb-2">¿Cómo fue tu experiencia?</h3>
            <p className="text-muted text-sm">Nos encantaría saber qué opinas del estudio, las clases y el servicio. Tu opinión es muy valiosa para nosotros.</p>
          </div>
          
          <div className="md:w-2/3 space-y-4">
            <div>
              <p className="text-sm font-semibold text-foreground mb-2">Calificación</p>
              <div className="flex gap-2" onMouseLeave={() => setHoverRating(0)}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <motion.button
                    key={star}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoverRating(star)}
                    className={`text-3xl transition-colors ${
                      star <= (hoverRating || rating) ? 'text-yellow-400' : 'text-gray-200'
                    }`}
                  >
                    ★
                  </motion.button>
                ))}
              </div>
            </div>
            
            <div>
              <p className="text-sm font-semibold text-foreground mb-2">Comentario (opcional)</p>
              <textarea 
                className="w-full rounded-xl border border-violett-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-violett-500 bg-gray-50/50 resize-none"
                rows={3}
                placeholder="¿Qué fue lo que más te gustó?"
                value={comment}
                onChange={e => setComment(e.target.value)}
              ></textarea>
            </div>
            
            <div className="flex justify-end">
              <Button onClick={handleSubmit} disabled={isSubmitting} className="w-full md:w-auto">
                {isSubmitting ? 'Enviando...' : 'Enviar Reseña'}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
"""
with open('frontend/src/components/ui/ReviewForm.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
print("Review component created with utf-8")
