import React, { useState, useEffect } from 'react';
import { getAdminAgenda, updateAsistencia } from '../../lib/adminApi';
import type { TurnoAdmin } from '../../lib/adminApi';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';

export function AgendaAdmin() {
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0]);
  const [turnos, setTurnos] = useState<TurnoAdmin[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAgenda = async () => {
    try {
      setLoading(true);
      const res = await getAdminAgenda(fecha);
      setTurnos(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgenda();
  }, [fecha]);

  const handleAsistencia = async (reservaId: string, estado: 'TOMADA' | 'AUSENTE') => {
    try {
      await updateAsistencia(reservaId, estado);
      fetchAgenda();
    } catch (e) {
      alert("Error actualizando asistencia");
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <h2 className="text-3xl font-bold text-violett-900">Turnos del Día</h2>
      
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            <input 
              type="date" 
              value={fecha} 
              onChange={(e) => setFecha(e.target.value)}
              className="p-2.5 rounded-xl border border-violett-200 text-foreground bg-white focus:outline-none focus:ring-2 focus:ring-violett-500 shadow-sm"
            />
            <Button onClick={() => setFecha(new Date().toISOString().split('T')[0])}>
              Hoy
            </Button>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <p className="text-muted py-4">Cargando turnos...</p>
      ) : turnos.length === 0 ? (
        <p className="text-muted py-4">No hay turnos para esta fecha.</p>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-violett-50/50">
                  <tr>
                    <th className="py-4 px-6 text-sm font-bold text-violett-900">Hora</th>
                    <th className="py-4 px-6 text-sm font-bold text-violett-900">Clase</th>
                    <th className="py-4 px-6 text-sm font-bold text-violett-900">Inscriptos</th>
                    <th className="py-4 px-6 text-sm font-bold text-violett-900 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  <AnimatePresence>
                    {turnos.map((turno) => (
                      <motion.tr 
                        key={turno.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="border-t border-violett-100 bg-white"
                      >
                        <td className="py-4 px-6 align-top">
                          <span className="font-bold text-lg text-foreground">{turno.hora_inicio.slice(0,5)}</span>
                        </td>
                        <td className="py-4 px-6 align-top">
                          <span className="text-violett-900 font-bold">{turno.clase_nombre}</span>
                          <br/>
                          <span className="text-sm text-muted">Prof: {turno.profesor ? turno.profesor.nombre : 'Sin asignar'}</span>
                        </td>
                        <td className="py-4 px-6">
                          {turno.reservas_list.length > 0 ? (
                            <ul className="space-y-4">
                              {turno.reservas_list.map((r) => (
                                <li key={r.id} className="flex flex-col gap-2 border-b border-violett-50 pb-4 last:border-0 last:pb-0">
                                  <div>
                                    <p className="font-medium text-foreground">{r.alumno_nombre} {r.alumno_apellido}</p>
                                    <p className="text-xs text-muted">{r.es_recurrente ? 'Recurrente' : 'Puntual'}</p>
                                  </div>
                                  <div className="flex gap-2">
                                    <Button 
                                      size="sm"
                                      variant={r.estado === 'TOMADA' ? 'default' : 'outline'}
                                      className={r.estado === 'TOMADA' ? 'bg-emerald-600 hover:bg-emerald-700 shadow-none' : 'text-emerald-700 border-emerald-200 hover:bg-emerald-50'}
                                      onClick={() => handleAsistencia(r.id, 'TOMADA')}
                                    >
                                      ✓ Presente
                                    </Button>
                                    <Button 
                                      size="sm"
                                      variant={r.estado === 'AUSENTE' ? 'default' : 'outline'}
                                      className={r.estado === 'AUSENTE' ? 'bg-rose-600 hover:bg-rose-700 shadow-none' : 'text-rose-700 border-rose-200 hover:bg-rose-50'}
                                      onClick={() => handleAsistencia(r.id, 'AUSENTE')}
                                    >
                                      ✗ Ausente
                                    </Button>
                                  </div>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-sm text-muted">Sin inscriptos</span>
                          )}
                        </td>
                        <td className="py-4 px-6 align-top text-right space-y-2">
                          <Button className="w-full" variant="outline">Modificar</Button>
                          <Button className="w-full bg-red-500 hover:bg-red-600 text-white">Cancelar</Button>
                        </td>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}
