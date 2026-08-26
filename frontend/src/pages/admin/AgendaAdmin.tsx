import React, { useState, useEffect } from 'react';
import { Skeleton } from "../../components/ui/Skeleton";
import { toast } from "sonner";
import { Modal } from '../../components/ui/Modal';
import { getAdminAgenda, updateAsistencia, createAdminTurno, getAdminClases, getAdminProfesores } from '../../lib/adminApi';
import type { TurnoAdmin } from '../../lib/adminApi';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { FeedbackButton } from '../../components/ui/FeedbackButton';
import { Badge } from '../../components/ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';

export function AgendaAdmin() {
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0]);
  const [turnos, setTurnos] = useState<TurnoAdmin[]>([]);
  const [expandedIds, setExpandedIds] = useState<string[]>([]);

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const [loading, setLoading] = useState(true);

  const [clases, setClases] = useState<any[]>([]);
  const [profesores, setProfesores] = useState<any[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({ clase: "", profesor: "", fecha: fecha, hora_inicio: "10:00", hora_fin: "11:00" });

  const todayStr = new Date().toISOString().split('T')[0];
  const getFechaTitle = () => {
    if (fecha === todayStr) return 'Hoy';
    const [year, month, day] = fecha.split('-').map(Number);
    const d = new Date(year, month - 1, day);
    return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'long' });
  };

  const fetchAuxData = async () => {
    try {
      const [resClases, resProfesores] = await Promise.all([getAdminClases(), getAdminProfesores()]);
      setClases(resClases.data);
      setProfesores(resProfesores.data);
    } catch(e) {}
  };
  useEffect(() => { fetchAuxData(); }, []);

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

  const handleAsistencia = async (reservaId: string, estado: 'TOMADA' | 'AUSENTE' | 'CONFIRMADA') => {
    try {
      await updateAsistencia(reservaId, estado);
      
      // Update local state without refetching to avoid skeletons and flickering
      setTurnos(prev => prev.map(turno => ({
        ...turno,
        reservas_list: turno.reservas_list?.map((res: any) => 
          res.id === reservaId ? { ...res, estado } : res
        )
      })));
      
    } catch (e) {
      toast.error("Error actualizando asistencia");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createAdminTurno({
        clase: formData.clase,
        profesor: formData.profesor || null,
        fecha: formData.fecha,
        hora_inicio: formData.hora_inicio,
        hora_fin: formData.hora_fin
      });
      setIsModalOpen(false);
      fetchAgenda();
    } catch (e) {
      toast.error("Error creando el turno puntual")
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-3xl font-bold text-violett-900">Agenda</h2>
        <Button onClick={() => setIsModalOpen(true)}>+ Agregar Clase</Button>
      </div>
      
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            <input 
              type="date" 
              value={fecha} 
              onChange={(e) => setFecha(e.target.value)}
              className="p-2.5 rounded-xl border border-violett-200 text-foreground bg-white focus:outline-none focus:ring-2 focus:ring-violett-500 shadow-sm"
            />
            <Button variant={fecha === todayStr ? 'default' : 'outline'} onClick={() => setFecha(todayStr)}>
              {getFechaTitle()}
            </Button>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="space-y-4 mt-4">
            {[1,2,3,4].map(i => <Skeleton key={i} className="h-16 w-full" />)}
          </div>
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
                          <br/>
                          <span className="text-xs font-semibold text-emerald-600 mt-1 inline-block">
                            Asistencia: {turno.reservas_list.filter((r: any) => r.estado === 'TOMADA').length}/{turno.reservas_list.length}
                          </span>
                        </td>
                                                <td className="py-4 px-6 align-top">
                          {turno.reservas_list.length > 0 ? (
                            <div className="space-y-3">
                              <button 
                                onClick={() => toggleExpand(turno.id)}
                                className="w-full text-left py-2 px-3 bg-violett-50/50 hover:bg-violett-100/50 rounded-xl font-medium text-sm text-violett-900 transition-colors flex justify-between items-center"
                              >
                                <span>{turno.reservas_list.length} inscriptos</span>
                                <span className="text-lg leading-none">{expandedIds.includes(turno.id) ? '▾' : '▸'}</span>
                              </button>
                              <AnimatePresence initial={false}>
                                {expandedIds.includes(turno.id) && (
                                  <motion.ul 
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.3 }}
                                    className="space-y-4 overflow-hidden px-1"
                                  >
                                    {turno.reservas_list.map((r: any) => (
                                      <li key={r.id} className="flex flex-col gap-2 border-b border-violett-50 pb-4 last:border-0 last:pb-0">
                                        <div>
                                          <p className="font-medium text-foreground">{r.alumno_nombre} {r.alumno_apellido}</p>
                                          <p className="text-xs text-muted">{r.es_recurrente ? 'Recurrente' : 'Puntual'}</p>
                                        </div>
                                        <motion.div layout className="flex gap-2 w-full max-w-[220px]">
                                          <AnimatePresence initial={false}>
                                            {(r.estado === 'CONFIRMADA' || r.estado === 'TOMADA') && (
                                              <motion.div 
                                                key="presente"
                                                layout
                                                initial={{ opacity: 0, flex: 0 }} 
                                                animate={{ opacity: 1, flex: r.estado === 'TOMADA' ? '1 1 100%' : '1 1 50%' }} 
                                                exit={{ opacity: 0, flex: 0, padding: 0, margin: 0, overflow: 'hidden' }} 
                                                transition={{ type: 'spring', bounce: 0, duration: 0.6 }}
                                                className="flex"
                                              >
                                                <FeedbackButton 
                                                  size="sm" 
                                                  variant={r.estado === 'TOMADA' ? 'default' : 'outline'}
                                                  key={`presente-btn-${r.estado}`}
                                                  onClick={() => handleAsistencia(r.id, r.estado === 'TOMADA' ? 'CONFIRMADA' : 'TOMADA')}
                                                  className={r.estado !== 'TOMADA' ? "w-full flex-1 whitespace-nowrap bg-white hover:bg-violett-50 text-violett-900 border-violett-200 hover:border-violett-300" : "w-full flex-1 whitespace-nowrap bg-violett-900 hover:bg-violett-800 border-violett-900 text-white"}
                                                  initialText={r.estado === 'TOMADA' ? '✓ Presente (Deshacer)' : 'Presente'}
                                                  successText={r.estado === 'TOMADA' ? 'Deshecho' : 'Asistió'}
                                                />
                                              </motion.div>
                                            )}
                                            {(r.estado === 'CONFIRMADA' || r.estado === 'AUSENTE') && (
                                              <motion.div 
                                                key="ausente"
                                                layout
                                                initial={{ opacity: 0, flex: 0 }} 
                                                animate={{ opacity: 1, flex: r.estado === 'AUSENTE' ? '1 1 100%' : '1 1 50%' }} 
                                                exit={{ opacity: 0, flex: 0, padding: 0, margin: 0, overflow: 'hidden' }} 
                                                transition={{ type: 'spring', bounce: 0, duration: 0.6 }}
                                                className="flex"
                                              >
                                                <FeedbackButton 
                                                  size="sm" 
                                                  variant={r.estado === 'AUSENTE' ? 'destructive' : 'outline'}
                                                  key={`ausente-btn-${r.estado}`}
                                                  onClick={() => handleAsistencia(r.id, r.estado === 'AUSENTE' ? 'CONFIRMADA' : 'AUSENTE')}
                                                  className={r.estado !== 'AUSENTE' ? "w-full flex-1 whitespace-nowrap bg-white hover:bg-rose-50 text-rose-500 border-rose-200 hover:border-rose-300" : "w-full flex-1 whitespace-nowrap text-white bg-rose-500 hover:bg-rose-600 border-rose-500"}
                                                  initialText={r.estado === 'AUSENTE' ? '✗ Ausente (Deshacer)' : 'Ausente'}
                                                  successText={r.estado === 'AUSENTE' ? 'Deshecho' : 'Faltó'}
                                                />
                                              </motion.div>
                                            )}
                                          </AnimatePresence>
                                        </motion.div>
                                      </li>
                                    ))}
                                  </motion.ul>
                                )}
                              </AnimatePresence>
                            </div>
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

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Crear Turno Puntual">
        <form onSubmit={handleCreate} className="space-y-4">
                    <div>
            <label className="block text-sm font-semibold mb-1">Clase</label>
            <select required value={formData.clase} onChange={e => setFormData({...formData, clase: e.target.value})} className="w-full p-2 border rounded-xl bg-white">
              <option value="">Selecciona una clase</option>
              {clases.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">Profesor (Opcional)</label>
            <select value={formData.profesor} onChange={e => setFormData({...formData, profesor: e.target.value})} className="w-full p-2 border rounded-xl bg-white">
              <option value="">Dejar libre (Bolsa de trabajo)</option>
              {profesores.map(p => <option key={p.id} value={p.id}>{p.nombre} {p.apellido}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">Fecha</label>
            <input type="date" required value={formData.fecha} onChange={e => setFormData({...formData, fecha: e.target.value})} className="w-full p-2 border rounded-xl" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-1">Hora Inicio</label>
              <input type="time" required value={formData.hora_inicio} onChange={e => setFormData({...formData, hora_inicio: e.target.value})} className="w-full p-2 border rounded-xl" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1">Hora Fin</label>
              <input type="time" required value={formData.hora_fin} onChange={e => setFormData({...formData, hora_fin: e.target.value})} className="w-full p-2 border rounded-xl" />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>Cancelar</Button>
            <Button type="submit">Guardar Turno</Button>
          </div>
        </form>
      </Modal>
    </motion.div>
  );
}



