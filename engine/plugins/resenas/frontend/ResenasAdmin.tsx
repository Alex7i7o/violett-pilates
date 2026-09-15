import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../../../frontend/src/components/ui/Card';
import { api } from '../../../frontend/src/lib/api';
import { toast } from 'sonner';

export function ResenasAdmin() {
  const [resenas, setResenas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResenas();
  }, []);

  const fetchResenas = async () => {
    try {
      const res = await api.get('/resenas/');
      setResenas(res.data);
    } catch (e) {
      toast.error('Error al cargar reseñas');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted">Cargando reseñas...</div>;
  }

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-primary-main">Reseñas de Alumnas</h1>
      </div>

      {resenas.length === 0 ? (
        <p className="text-muted">Aún no hay reseñas registradas.</p>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {resenas.map((resena) => (
            <Card key={resena.id} className="shadow-sm border-primary-light">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex text-yellow-400 text-lg">
                    {'★'.repeat(resena.estrellas)}
                    {'☆'.repeat(5 - resena.estrellas)}
                  </div>
                  <span className="text-xs text-muted">
                    {new Date(resena.fecha).toLocaleDateString()}
                  </span>
                </div>
                
                {resena.mensaje && (
                  <p className="text-foreground italic mb-4">"{resena.mensaje}"</p>
                )}
                
                <p className="text-sm font-semibold text-primary-main text-right">
                  - {resena.autor}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
