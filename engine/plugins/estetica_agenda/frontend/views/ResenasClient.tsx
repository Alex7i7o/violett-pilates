import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import {
  Card,
  CardTitle,
  CardDescription,
  Button,
  FeedbackButton,
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
        <h1 className="text-2xl sm:text-3xl font-bold text-[#FFF8EE] font-serif mb-1">
          Experiencias & Reseñas
        </h1>
        <p className="text-xs sm:text-sm text-[#FFF8EE]/60">
          Tu testimonio nos impulsa a seguir brindándote la máxima excelencia estética.
        </p>
      </div>

      {/* Formulario de Reseña */}
      <Card variant="elevated" className="bg-[#190826]/90 border border-[#C5A059]/25 p-6 sm:p-8 rounded-2xl">
        <div className="flex items-center gap-3 mb-5">
          <div className="p-2.5 bg-[#C5A059]/15 border border-[#C5A059]/30 text-[#C5A059] rounded-xl">
            <MessageSquareQuote size={20} />
          </div>
          <div>
            <CardTitle className="text-lg font-bold text-[#FFF8EE] font-serif">Dejanos tu opinión</CardTitle>
            <CardDescription className="text-xs text-[#FFF8EE]/60">Compartí tu experiencia en Violett Estética</CardDescription>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#C5A059] mb-2">
              Calificación general
            </label>
            <StarRating
              value={estrellas}
              onChange={val => {
                haptics.selection();
                setEstrellas(val);
              }}
              size="lg"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#C5A059] mb-2">
              Tu Comentario
            </label>
            <textarea
              value={mensaje}
              onChange={e => setMensaje(e.target.value)}
              className="w-full p-4 rounded-xl bg-white/5 border border-white/15 text-[#FFF8EE] placeholder:text-[#FFF8EE]/30 outline-none focus:border-[#C5A059] h-28 resize-none text-sm transition-all"
              placeholder="¿Qué te pareció el tratamiento, la atención y el espacio?"
            ></textarea>
          </div>

          <Button
            type="submit"
            variant="glow"
            size="md"
            disabled={submitting}
            className="!bg-[#C5A059] !text-[#150720] hover:!bg-[#B38E4C] font-bold text-xs px-6 py-3 rounded-full"
          >
            {submitting ? 'Enviando...' : 'Publicar Reseña'}
          </Button>
        </form>
      </Card>

      {/* Listado de Reseñas */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-[#FFF8EE] font-serif">Lo que dicen nuestras clientas</h2>

        {loading ? (
          <div className="space-y-3">
            {[1, 2].map(i => (
              <div key={i} className="h-24 bg-white/5 border border-white/10 rounded-2xl animate-pulse"></div>
            ))}
          </div>
        ) : resenas.length === 0 ? (
          <EmptyState
            title="Aún no hay reseñas publicadas"
            description="¡Sé la primera en compartir tu experiencia en Violett Estética!"
            icon={<Star size={24} className="text-[#C5A059]" />}
            className="border-[#C5A059]/20 bg-[#190826]/70 rounded-2xl p-8"
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {resenas.map(r => {
              const fullName = `${r.usuario_detalle?.nombre || ''} ${r.usuario_detalle?.apellido || ''}`.trim() || 'Clienta';
              return (
                <Card
                  key={r.id}
                  variant="default"
                  className="bg-[#190826]/80 border border-[#C5A059]/20 p-5 rounded-2xl flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-3 mb-3">
                      <div className="flex items-center gap-3">
                        <Avatar
                          name={fullName}
                          size="md"
                          className="bg-[#C5A059]/20 text-[#C5A059] border border-[#C5A059]/30 font-bold"
                        />
                        <div>
                          <p className="font-bold text-sm text-[#FFF8EE] font-serif">{fullName}</p>
                          <StarRating value={r.estrellas} readOnly size="sm" />
                        </div>
                      </div>
                    </div>

                    {r.mensaje && (
                      <p className="text-xs text-[#FFF8EE]/80 leading-relaxed italic bg-white/5 p-3 rounded-xl border border-white/5 mt-2">
                        "{r.mensaje}"
                      </p>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};