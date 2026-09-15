import { ConfirmModal } from '../../components/ui/ConfirmModal';
import React, { useState, useEffect } from 'react';
import { Skeleton } from "../../components/ui/Skeleton";
import { toast } from "sonner";
import { Modal } from '../../components/ui/Modal';
import { getAdminAgenda, updateAsistencia, createAdminTurno, updateAdminTurno, deleteAdminTurno, getAdminClases, getAdminProfesores } from '../../lib/adminApi';
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
  const [editingTurnoId, setEditingTurnoId] = useState<string | null>(null);
  const [turnoToDelete, setTurnoToDelete] = useState<string | null>(null);
  const [formData, setFormData] = useState({ clase: "", profesor: "", fecha: fecha, hora_inicio: "10:00", hora_fin: "11:00" });

  useEffect(() => {
    if (formData.hora_inicio) {
      const selectedClase = clases.find((c: any) => c.id.toString() === formData.clase.toString());
      const duration = (selectedClase && selectedClase.duracion_minutos) ? selectedClase.duracion_minutos : 60;
      
      const [hours, minutes] = formData.hora_inicio.split(':').map(Number);
      const totalMinutes = hours * 60 + minutes + duration;
      const endHours = Math.floor(totalMinutes / 60) % 24;
      const endMinutes = totalMinutes % 60;
      const newHoraFin = `${String(endHours).padStart(2, '0')}:${String(endMinutes).padStart(2, '0')}`;
      
      setFormData(prev => {
        if (prev.hora_fin !== newHoraFin) {
          return { ...prev, hora_fin: newHoraFin };
        }
        return prev;
      });
    }
  }, [formData.hora_inicio, formData.clase, clases]);


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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        clase: formData.clase,
        profesor: formData.profesor || null,
        fecha: formData.fecha,
        hora_inicio: formData.hora_inicio,
        hora_fin: formData.hora_fin
      };
      if (editingTurnoId) {
        await updateAdminTurno(editingTurnoId, data);
        toast.success("Turno modificado correctamente");
      } else {
        await createAdminTurno(data);
        toast.success("Turno creado correctamente");
      }
      setIsModalOpen(false);
      setEditingTurnoId(null);
      fetchAgenda();
    } catch (e) {
      toast.error("Error al guardar el turno");
    }
  };

  const handleEditClick = (turno: any) => {
    setEditingTurnoId(turno.id);
    setFormData({
      clase: turno.clase,
      profesor: turno.profesor || "",
      fecha: turno.fecha,
      hora_inicio: turno.hora_inicio,
      hora_fin: turno.hora_fin
    });
    setIsModalOpen(true);
  };

  const handleDeleteTurno = async () => {
    if (!turnoToDelete) return;
    try {
      await deleteAdminTurno(turnoToDelete);
      toast.success("Turno cancelado correctamente");
      fetchAgenda();
    } catch (e) {
      toast.error("Error al cancelar el turno");
    } finally {
      setTurnoToDelete(null);
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-3xl font-bold text-primary-main">Agenda</h2>
        <Button onClick={() => { setEditingTurnoId(null); setFormData({ clase: "", profesor: "", fecha: fecha, hora_inicio: "10:00", hora_fin: "11:00" }); setIsModalOpen(true); }}>+ Agregar Clase</Button>
      </div>
      
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            <input 
              type="date" 
              value={fecha} 
              onChange={(e) => setFecha(e.target.value)}
              className="p-2.5 rounded-xl border border-primary-light text-foreground bg-white focus:outline-none focus:ring-2 focus:ring-primary-main shadow-sm"
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
            <AnimatePresence>
              {turnos.map((turno) => (
                <motion.div 
                  key={turno.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  layout
                  className="w-full"
                >
                  <Card className="hover:shadow-md transition-shadow h-full flex flex-col border-primary-light/50">
                    <CardContent className="p-5 flex flex-col h-full">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <span className="font-bold text-2xl text-foreground mb-1 block">{turno.hora_inicio.slice(0,5)}</span>
                          <span className="text-primary-main font-bold block">{turno.clase_nombre}</span>
                          <span className="text-sm text-muted mt-1 block">
                            {turno.profesor_nombre ? "Prof: " + turno.profesor_nombre + " " + (turno.profesor_apellido || "") : "Sin asignar"}
                          </span>
                        </div>
                        <div className="text-right flex flex-col items-end">
                           <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-1 rounded-md mt-1">
                             Asistencia: {turno.reservas_list.filter((r: any) => r.estado === 'TOMADA').length}/{turno.reservas_list.length}
                           </span>
                        </div>
                      </div>
                      
                      <div className="flex-1 mt-2 mb-6 bg-slate-50/50 rounded-xl p-3 border border-slate-100">
                        {turno.reservas_list.length > 0 ? (
                          <div className="space-y-3">
                            <button 
                              onClick={() => toggleExpand(turno.id)}
                              className="w-full text-left py-2 px-3 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl font-medium text-sm text-slate-700 transition-colors flex justify-between items-center shadow-sm"
                            >
                              <span>{turno.reservas_list.length} inscriptos</span>
                              <span className="text-lg leading-none text-slate-400">{expandedIds.includes(turno.id) ? '▾' : '▸'}</span>
                            </button>
                            <AnimatePresence initial={false}>
                              {expandedIds.includes(turno.id) && (
                                <motion.ul 
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: 'auto', opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  transition={{ duration: 0.2 }}
                                  className="space-y-3 overflow-hidden px-1 pt-2"
                                >
                                  {turno.reservas_list.map((r: any) => (
                                    <li key={r.id} className="flex flex-col gap-2 border-b border-slate-200 pb-3 last:border-0 last:pb-0">
                                      <div className="flex justify-between items-center">
                                        <p className="font-medium text-sm text-foreground">{r.alumno_nombre} {r.alumno_apellido}</p>
                                        <span className="text-[10px] uppercase font-bold text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">{r.es_recurrente ? 'Rec' : 'Pun'}</span>
                                      </div>
                                      <motion.div layout className="flex gap-2 w-full">
                                        {r.estado === 'CONFIRMADA' && (
                                          <Button size="sm" className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-[11px] h-7 text-white" onClick={() => updateReservaStatus(r.id, 'TOMADA')}>Asistió</Button>
                                        )}
                                        {r.estado === 'CONFIRMADA' && (
                                          <Button size="sm" variant="outline" className="flex-1 text-red-500 border-red-200 hover:bg-red-50 text-[11px] h-7" onClick={() => updateReservaStatus(r.id, 'AUSENTE')}>Ausente</Button>
                                        )}
                                        {r.estado !== 'CONFIRMADA' && (
                                          <div className="w-full text-center py-1">
                                            <span className={`text-xs font-semibold ${r.estado === 'TOMADA' ? 'text-emerald-600' : 'text-red-500'}`}>
                                              {r.estado === 'TOMADA' ? '✓ Asistió' : '✕ Ausente'}
                                            </span>
                                          </div>
                                        )}
                                      </motion.div>
                                    </li>
                                  ))}
                                </motion.ul>
                              )}
                            </AnimatePresence>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center h-full min-h-[60px]">
                            <span className="text-sm text-muted italic">Sin inscriptos</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex justify-end gap-2 mt-auto pt-4 border-t border-primary-light/50">
                        <Button size="sm" variant="outline" className="flex-1" onClick={() => handleEditClick(turno)}>Modificar</Button>
                        <Button size="sm" variant="outline" className="flex-1 text-red-500 border-red-200 hover:bg-red-50 hover:text-red-600" onClick={() => setTurnoToDelete(turno.id)}>Cancelar</Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingTurnoId ? "Modificar Turno" : "Crear Turno Puntual"}>
        <form 
      onInvalid={(e) => {
        e.preventDefault();
        const t = typeof toast !== 'undefined' ? toast : (window as any).toast;
        if(t) t.error('Por favor, completa todos los campos requeridos.');
      }}
      onSubmit={handleSubmit} className="space-y-4">
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

      <ConfirmModal
        isOpen={!!turnoToDelete}
        onClose={() => setTurnoToDelete(null)}
        onConfirm={handleDeleteTurno}
        title="Cancelar Turno"
        message="¿Estás seguro de cancelar este turno? Las alumnas inscriptas recuperarán su clase."
        confirmText="Sí, Cancelar"
        cancelText="No, Volver"
        isDestructive={true}
      />
    </motion.div>

  );
}



