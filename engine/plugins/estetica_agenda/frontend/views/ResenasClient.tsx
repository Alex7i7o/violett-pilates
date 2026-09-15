import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { Star } from 'lucide-react';

export const ResenasClient = () => {
  const [resenas, setResenas] = useState<any[]>([]);
  const [estrellas, setEstrellas] = useState(5);
  const [mensaje, setMensaje] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchResenas = () => {
    api.get('/resenas/')
      .then(res => setResenas(res.data))
      .catch(() => toast.error('Error cargando reseñas'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchResenas();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/resenas/', { estrellas, mensaje });
      toast.success('¡Gracias por tu reseña!');
      setMensaje('');
      setEstrellas(5);
      fetchResenas();
    } catch (error) {
      toast.error('Error al enviar la reseña');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full">
      <h1 className="text-2xl font-bold text-neutral-800 mb-8 flex items-center gap-2">
        ⭐ Reseñas
      </h1>

      <div className="bg-neutral-50 p-6 rounded-2xl mb-8 border border-neutral-100">
        <h2 className="font-bold text-lg mb-4 text-neutral-800">Dejanos tu opinión</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-600 mb-2">Calificación</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map(num => (
                <button
                  type="button"
                  key={num}
                  onClick={() => setEstrellas(num)}
                  className={`p-2 rounded-full transition-colors ${estrellas >= num ? 'text-yellow-500' : 'text-neutral-300'}`}
                >
                  <Star fill={estrellas >= num ? "currentColor" : "none"} size={28} />
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-600 mb-2">Comentario (opcional)</label>
            <textarea 
              value={mensaje}
              onChange={e => setMensaje(e.target.value)}
              className="w-full p-3 rounded-xl border border-neutral-200 outline-none focus:border-primary-main h-24 resize-none"
              placeholder="¿Qué te pareció nuestro servicio?"
            ></textarea>
          </div>
          <button 
            type="submit" 
            disabled={submitting}
            className="px-6 py-3 bg-neutral-800 text-white font-bold rounded-xl hover:bg-neutral-900 transition-colors disabled:opacity-50"
          >
            {submitting ? 'Enviando...' : 'Publicar Reseña'}
          </button>
        </form>
      </div>

      <h2 className="font-bold text-lg mb-4 text-neutral-800">Lo que dicen nuestras clientas</h2>
      {loading ? (
        <p className="text-neutral-500">Cargando...</p>
      ) : resenas.length === 0 ? (
        <p className="text-neutral-500">Aún no hay reseñas. ¡Sé la primera!</p>
      ) : (
        <div className="space-y-4">
          {resenas.map(r => (
            <div key={r.id} className="bg-white p-5 rounded-2xl border border-neutral-100 shadow-sm">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-primary-100 text-primary-main rounded-full flex items-center justify-center font-bold text-lg">
                  {r.usuario_detalle?.nombre?.[0] || 'A'}
                </div>
                <div>
                  <p className="font-bold text-neutral-800">{r.usuario_detalle?.nombre} {r.usuario_detalle?.apellido}</p>
                  <div className="flex gap-1 text-yellow-500">
                    {[...Array(r.estrellas)].map((_, i) => <Star key={i} size={14} fill="currentColor" />)}
                  </div>
                </div>
              </div>
              {r.mensaje && <p className="text-neutral-600 text-sm mt-3">{r.mensaje}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
