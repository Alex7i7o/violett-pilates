import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import {
  Button,
  StarRating,
  Avatar,
  EmptyState,
  haptics
} from 'fireseed-ui';
import { Star, MessageSquareQuote } from 'lucide-react';

export const ResenasClient = () => {
  const [resenas, setResenas] = useState<any[]>([]);
  const [estrellas, setEstrellas] = useState(5);
  const [mensaje, setMensaje] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchResenas = () => {
    api.get('/resenas/')
      .then(res => setResenas(res.data || []))
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
    } catch {
      toast.error('Error al enviar la reseña');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full pb-24 space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-[#34236F] font-serif mb-1">
          Experiencias & Reseñas
        </h1>
        <p className="text-xs sm:text-sm text-neutral-500">
          Tu testimonio nos impulsa a seguir brindándote la máxima excelencia estética.
        </p>
      </div>

      {/* Formulario de Reseña */}
      <div className="bg-white border border-neutral-100 shadow-soft p-6 sm:p-8 rounded-2xl">
        <div className="flex items-center gap-3 mb-5">
          <div className="p-2.5 bg-[#F9F6ED] border border-[#C5A059]/30 text-[#C5A059] rounded-xl">
            <MessageSquareQuote size={20} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#34236F] font-serif">Dejanos tu opinión</h3>
            <p className="text-xs text-neutral-500">Compartí tu experiencia en Violett Estética</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#34236F] mb-2">
              Calificación general
            </label>
            <StarRating
              value={estrellas}
              onChange={val => {
                haptics.light();
                setEstrellas(val);
              }}
              size="lg"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#34236F] mb-2">
              Tu Comentario
            </label>
            <textarea
              value={mensaje}
              onChange={e => setMensaje(e.target.value)}
              className="w-full p-4 rounded-xl bg-white border border-neutral-200 text-[#34236F] placeholder:text-neutral-400 outline-none focus:border-[#C5A059] h-28 resize-none text-sm transition-all"
              placeholder="¿Qué te pareció el tratamiento, la atención y el espacio?"
            ></textarea>
          </div>

          <Button
            type="submit"
            variant="glow"
            size="md"
            disabled={submitting}
            className="!bg-[#C5A059] hover:!bg-[#B38E4C] !text-white font-bold text-xs px-6 py-3 rounded-full"
          >
            {submitting ? 'Enviando...' : 'Publicar Reseña'}
          </Button>
        </form>
      </div>

      {/* Listado de Reseñas */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-[#34236F] font-serif">Lo que dicen nuestras clientas</h2>

        {loading ? (
          <div className="space-y-3">
            {[1, 2].map(i => (
              <div key={i} className="h-24 bg-white border border-neutral-100 rounded-2xl animate-pulse shadow-soft"></div>
            ))}
          </div>
        ) : resenas.length === 0 ? (
          <div className="bg-white border border-neutral-100 rounded-2xl p-8 text-center shadow-soft">
            <Star size={28} className="text-[#C5A059] mx-auto mb-2" />
            <p className="text-neutral-700 font-semibold mb-1">Aún no hay reseñas publicadas</p>
            <p className="text-xs text-neutral-400">¡Sé la primera en compartir tu experiencia en Violett Estética!</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {resenas.map(r => {
              const fullName = `${r.usuario_detalle?.nombre || ''} ${r.usuario_detalle?.apellido || ''}`.trim() || 'Clienta';
              return (
                <div
                  key={r.id}
                  className="bg-white border border-neutral-100 shadow-soft p-5 rounded-2xl flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-3 mb-3">
                      <div className="flex items-center gap-3">
                        <Avatar
                          name={fullName}
                          size="md"
                          className="bg-[#F9F6ED] text-[#C5A059] border border-[#C5A059]/30 font-bold"
                        />
                        <div>
                          <p className="font-bold text-sm text-[#34236F] font-serif">{fullName}</p>
                          <StarRating value={r.estrellas} readOnly size="sm" />
                        </div>
                      </div>
                    </div>

                    {r.mensaje && (
                      <p className="text-xs text-neutral-600 leading-relaxed italic bg-neutral-50 p-3 rounded-xl border border-neutral-100 mt-2">
                        "{r.mensaje}"
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};