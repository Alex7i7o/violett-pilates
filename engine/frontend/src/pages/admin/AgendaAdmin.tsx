import { ConfirmModal } from '../../components/ui/ConfirmModal';
import { MultiSelectAlumnos } from '../../components/admin/MultiSelectAlumnos';
import React, { useState, useEffect } from 'react';
import { Skeleton } from "../../components/ui/Skeleton";
import { toast } from "sonner";
import { Modal } from '../../components/ui/Modal';
import { 
  getAdminAgenda, 
  updateAsistencia, 
  createAdminTurno, 
  updateAdminTurno, 
  deleteAdminTurno, 
  getAdminClases, 
  getAdminProfesores,
  apartarCamillaManual,
  vincularReservaUsuario,
  liberarCamilla,
  getAdminAlumnos
} from '../../lib/adminApi';
import type { TurnoAdmin, ReservaAdmin, UsuarioAdmin } from '../../lib/adminApi';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
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
  const [deleteFuture, setDeleteFuture] = useState(false);
  const [formData, setFormData] = useState<{clase: string, profesor: string, fecha: string, hora_inicio: string, hora_fin: string, alumnos: string[]}>({ clase: "", profesor: "", fecha: fecha, hora_inicio: "10:00", hora_fin: "11:00", alumnos: [] });

  // Estados para apartar camilla manual (sin cuenta web)
  const [isApartarModalOpen, setIsApartarModalOpen] = useState(false);
  const [turnoParaApartar, setTurnoParaApartar] = useState<TurnoAdmin | null>(null);
  const [nombreManual, setNombreManual] = useState('');
  const [telefonoManual, setTelefonoManual] = useState('');
  const [isApartando, setIsApartando] = useState(false);

  // Estados para vincular reserva manual a cuenta registrada
  const [isVincularModalOpen, setIsVincularModalOpen] = useState(false);
  const [reservaParaVincular, setReservaParaVincular] = useState<ReservaAdmin | null>(null);
  const [alumnosList, setAlumnosList] = useState<UsuarioAdmin[]>([]);
  const [busquedaAlumno, setBusquedaAlumno] = useState('');
  const [alumnoSeleccionadoId, setAlumnoSeleccionadoId] = useState('');
  const [isVinculando, setIsVinculando] = useState(false);

  // Estados para liberar camilla manual
  const [reservaParaLiberar, setReservaParaLiberar] = useState<{ id: string; nombre: string } | null>(null);
  const [isLiberando, setIsLiberando] = useState(false);

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
      hora_fin: turno.hora_fin,
      alumnos: turno.reservas_list?.map((r: any) => r.alumno_id).filter(Boolean) || []
    });
    setIsModalOpen(true);
  };

  const handleDeleteTurno = async () => {
    if (!turnoToDelete) return;
    try {
      await deleteAdminTurno(turnoToDelete, deleteFuture);
      toast.success("Turno cancelado correctamente");
      fetchAgenda();
    } catch (e) {
      toast.error("Error al cancelar el turno");
    } finally {
      setTurnoToDelete(null);
      setDeleteFuture(false);
    }
  };

  // Handlers para apartado manual
  const handleAbrirApartar = (turno: TurnoAdmin) => {
    setTurnoParaApartar(turno);
    setNombreManual('');
    setTelefonoManual('');
    setIsApartarModalOpen(true);
  };

  const handleConfirmarApartar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!turnoParaApartar) return;
    const nom = nombreManual.trim();
    if (!nom) {
      toast.error('Por favor ingresa el nombre de la clienta.');
      return;
    }
    try {
      setIsApartando(true);
      await apartarCamillaManual(turnoParaApartar.id, nom, telefonoManual.trim());
      toast.success(`Camilla apartada para ${nom}`);
      setIsApartarModalOpen(false);
      setTurnoParaApartar(null);
      fetchAgenda();
    } catch (e: any) {
      console.error(e);
      toast.error(e.response?.data?.detail || 'Error al apartar camilla');
    } finally {
      setIsApartando(false);
    }
  };

  // Handlers para vincular a cuenta registrada
  const handleAbrirVincular = async (reserva: ReservaAdmin) => {
    setReservaParaVincular(reserva);
    setAlumnoSeleccionadoId('');
    setBusquedaAlumno('');
    setIsVincularModalOpen(true);
    try {
      const res = await getAdminAlumnos();
      setAlumnosList(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Error al cargar la lista de alumnas registradas');
    }
  };

  const handleConfirmarVincular = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reservaParaVincular || !alumnoSeleccionadoId) {
      toast.error('Selecciona una alumna de la lista');
      return;
    }
    try {
      setIsVinculando(true);
      await vincularReservaUsuario(reservaParaVincular.id, alumnoSeleccionadoId);
      const alumno = alumnosList.find(a => a.id === alumnoSeleccionadoId);
      toast.success(`Camilla vinculada a la cuenta de ${alumno?.nombre || 'la alumna'}`);
      setIsVincularModalOpen(false);
      setReservaParaVincular(null);
      fetchAgenda();
    } catch (e: any) {
      console.error(e);
      toast.error(e.response?.data?.detail || 'Error al vincular camilla a la cuenta');
    } finally {
      setIsVinculando(false);
    }
  };

  // Handlers para liberar camilla manual
  const handleConfirmarLiberar = async () => {
    if (!reservaParaLiberar) return;
    try {
      setIsLiberando(true);
      await liberarCamilla(reservaParaLiberar.id);
      toast.success('Camilla liberada. El cupo vuelve a estar disponible.');
      setReservaParaLiberar(null);
      fetchAgenda();
    } catch (e: any) {
      console.error(e);
      toast.error(e.response?.data?.detail || 'Error al liberar camilla');
    } finally {
      setIsLiberando(false);
    }
  };

  const alumnosFiltrados = alumnosList.filter(a => {
    const q = busquedaAlumno.toLowerCase().trim();
    if (!q) return true;
    return (
      (a.nombre || '').toLowerCase().includes(q) ||
      (a.apellido || '').toLowerCase().includes(q) ||
      (a.email || '').toLowerCase().includes(q) ||
      (a.telefono || '').includes(q)
    );
  });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-primary-main">Agenda</h2>
          <p className="text-xs text-muted mt-0.5">Control diario de clases, asistencia y apartado de camillas.</p>
        </div>
        <Button onClick={() => { setEditingTurnoId(null); setFormData({ clase: "", profesor: "", fecha: fecha, hora_inicio: "10:00", hora_fin: "11:00", alumnos: [] }); setIsModalOpen(true); }}>+ Agregar Clase</Button>
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
              {turnos.map((turno) => {
                const cuposLibres = turno.cupo_actual;
                const tieneCupo = cuposLibres > 0 && turno.estado === 'PROGRAMADO';

                return (
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
                          <div className="text-right flex flex-col items-end gap-1">
                             <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-1 rounded-md">
                               Asistencia: {turno.reservas_list.filter((r: any) => r.estado === 'TOMADA').length}/{turno.reservas_list.length}
                             </span>
                             <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md ${cuposLibres === 0 ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-slate-100 text-slate-700'}`}>
                               {cuposLibres === 0 ? 'Lleno' : `${cuposLibres} libre${cuposLibres > 1 ? 's' : ''}`}
                             </span>
                          </div>
                        </div>
                        
                        <div className="flex-1 mt-2 mb-4 bg-slate-50/50 rounded-xl p-3 border border-slate-100">
                          {turno.reservas_list.length > 0 ? (
                            <div className="space-y-3">
                              <button 
                                onClick={() => toggleExpand(turno.id)}
                                className="w-full text-left py-2 px-3 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl font-medium text-sm text-slate-700 transition-colors flex justify-between items-center shadow-sm"
                              >
                                <span>{turno.reservas_list.length} inscriptas</span>
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
                                    {turno.reservas_list.map((r: any) => {
                                      const isManual = r.tipo_reserva === 'MANUAL_TEMPORAL' || !r.alumno_id;

                                      return (
                                        <li key={r.id} className="flex flex-col gap-2 border-b border-slate-200 pb-3 last:border-0 last:pb-0">
                                          <div className="flex justify-between items-center">
                                            <div className="flex items-center gap-1.5 overflow-hidden">
                                              {isManual ? (
                                                <span className="text-xs shrink-0" title="Apartado Manual">🏷️</span>
                                              ) : (
                                                <span className="text-xs shrink-0" title="Alumna Registrada">👤</span>
                                              )}
                                              <p className={`font-semibold text-sm truncate ${isManual ? 'text-amber-950 font-bold' : 'text-foreground'}`}>
                                                {r.alumno_nombre} {r.alumno_apellido || ''}
                                              </p>
                                            </div>
                                            {isManual ? (
                                              <span className="text-[10px] uppercase font-bold text-amber-800 bg-amber-100 border border-amber-300 px-1.5 py-0.5 rounded shrink-0">
                                                ✦ Manual
                                              </span>
                                            ) : (
                                              <span className="text-[10px] uppercase font-bold text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded shrink-0">
                                                {r.es_recurrente ? 'Rec' : 'Pun'}
                                              </span>
                                            )}
                                          </div>

                                          {/* Acciones de Asistencia */}
                                          <motion.div layout className="flex flex-col gap-1.5 w-full">
                                            <div className="flex gap-2 w-full">
                                              {r.estado === 'CONFIRMADA' && (
                                                <Button size="sm" className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-[11px] h-7 text-white" onClick={() => handleAsistencia(r.id, 'TOMADA')}>Asistió</Button>
                                              )}
                                              {r.estado === 'CONFIRMADA' && (
                                                <Button size="sm" variant="outline" className="flex-1 text-red-500 border-red-200 hover:bg-red-50 text-[11px] h-7" onClick={() => handleAsistencia(r.id, 'AUSENTE')}>Ausente</Button>
                                              )}
                                              {r.estado !== 'CONFIRMADA' && (
                                                <div className="w-full text-center py-1">
                                                  <span className={`text-xs font-semibold ${r.estado === 'TOMADA' ? 'text-emerald-600' : 'text-red-500'}`}>
                                                    {r.estado === 'TOMADA' ? '✓ Asistió' : '✕ Ausente'}
                                                  </span>
                                                </div>
                                              )}
                                            </div>

                                            {/* Acciones exclusivas para camilla apartada manualmente */}
                                            {isManual && r.estado === 'CONFIRMADA' && (
                                              <div className="flex gap-2 w-full pt-1">
                                                <button 
                                                  type="button"
                                                  onClick={() => handleAbrirVincular(r)}
                                                  className="flex-1 text-[11px] py-1 px-2 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-semibold transition-colors flex items-center justify-center gap-1 shadow-2xs"
                                                >
                                                  <span>🔗</span> Vincular a cuenta
                                                </button>
                                                <button 
                                                  type="button"
                                                  onClick={() => setReservaParaLiberar({ id: r.id, nombre: r.alumno_nombre })}
                                                  className="text-[11px] py-1 px-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 font-semibold transition-colors"
                                                  title="Liberar esta camilla"
                                                >
                                                  ✕ Liberar
                                                </button>
                                              </div>
                                            )}
                                          </motion.div>
                                        </li>
                                      );
                                    })}
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
                        
                        {/* Botonera inferior del turno */}
                        <div className="flex flex-col gap-2 mt-auto pt-3 border-t border-primary-light/50">
                          {tieneCupo && (
                            <Button 
                              size="sm" 
                              variant="outline" 
                              onClick={() => handleAbrirApartar(turno)}
                              className="w-full text-xs font-bold text-amber-900 border-amber-300 bg-amber-50 hover:bg-amber-100 shadow-2xs transition-all flex items-center justify-center gap-1.5"
                            >
                              <span>✦</span> Apartar Camilla ({cuposLibres} disponible{cuposLibres > 1 ? 's' : ''})
                            </Button>
                          )}
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline" className="flex-1" onClick={() => handleEditClick(turno)}>Modificar</Button>
                            <Button size="sm" variant="outline" className="flex-1 text-red-500 border-red-200 hover:bg-red-50 hover:text-red-600" onClick={() => setTurnoToDelete(turno.id)}>Cancelar</Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal Crear / Modificar Turno */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingTurnoId ? "Modificar Turno" : "Crear Turno Puntual"}>
        <form 
          onInvalid={(e) => {
            e.preventDefault();
            toast.error('Por favor, completa todos los campos requeridos.');
          }}
          onSubmit={handleSubmit} 
          className="space-y-4"
        >
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

      {/* Modal Apartar Camilla Manual */}
      <Modal 
        isOpen={isApartarModalOpen} 
        onClose={() => setIsApartarModalOpen(false)} 
        title={turnoParaApartar ? `Apartar Camilla - ${turnoParaApartar.hora_inicio.slice(0,5)} hs` : "Apartar Camilla"}
      >
        <form onSubmit={handleConfirmarApartar} className="space-y-4 text-left">
          <div className="bg-amber-50 p-3.5 rounded-xl border border-amber-200 text-xs text-amber-900 leading-relaxed">
            <strong>✦ Apartado para clientas sin cuenta web:</strong><br />
            Esta camilla quedará bloqueada a nombre de la persona que indiques y se restará automáticamente del cupo. Nadie más podrá ocuparla por la web ni por WhatsApp.
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">
              Nombre de la Clienta *
            </label>
            <input 
              type="text" 
              required
              placeholder="Ej: Marcela Pérez o Cami amiga Débora"
              value={nombreManual}
              onChange={(e) => setNombreManual(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main bg-white text-sm"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">
              Teléfono (Opcional)
            </label>
            <input 
              type="text" 
              placeholder="Ej: 1123456789 (para WhatsApp)"
              value={telefonoManual}
              onChange={(e) => setTelefonoManual(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main bg-white text-sm"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsApartarModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isApartando} className="bg-amber-600 hover:bg-amber-700 text-white">
              {isApartando ? 'Apartando...' : 'Confirmar Apartado'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Vincular Camilla a Cuenta Registrada */}
      <Modal 
        isOpen={isVincularModalOpen} 
        onClose={() => setIsVincularModalOpen(false)} 
        title="Vincular a Cuenta de Alumna"
      >
        <form onSubmit={handleConfirmarVincular} className="space-y-4 text-left">
          <div className="bg-indigo-50 p-3.5 rounded-xl border border-indigo-200 text-xs text-indigo-900 leading-relaxed">
            Estás vinculando la camilla de <strong>{reservaParaVincular?.alumno_nombre}</strong> con su cuenta web real. Si tiene un abono activo con saldo, se le asociará y consumirá una clase.
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">
              Buscar Alumna Registrada
            </label>
            <input 
              type="text" 
              placeholder="Buscar por nombre, apellido o email..."
              value={busquedaAlumno}
              onChange={(e) => setBusquedaAlumno(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main bg-white text-sm mb-2"
            />
            
            <div className="max-h-56 overflow-y-auto border border-slate-200 rounded-xl divide-y divide-slate-100 bg-white">
              {alumnosFiltrados.length === 0 ? (
                <p className="text-xs text-muted p-4 text-center">No se encontraron alumnas con ese nombre.</p>
              ) : (
                alumnosFiltrados.map((a) => (
                  <label 
                    key={a.id} 
                    className={`flex items-center gap-3 p-3 text-xs cursor-pointer hover:bg-slate-50 transition-colors ${alumnoSeleccionadoId === a.id ? 'bg-indigo-50/70 font-semibold' : ''}`}
                  >
                    <input 
                      type="radio" 
                      name="alumno_vincular" 
                      value={a.id}
                      checked={alumnoSeleccionadoId === a.id}
                      onChange={() => setAlumnoSeleccionadoId(a.id)}
                      className="text-primary-main focus:ring-primary-main"
                    />
                    <div className="flex-1">
                      <p className="text-foreground font-medium text-sm">{a.nombre} {a.apellido}</p>
                      <p className="text-muted text-[11px]">{a.email} {a.telefono ? `• ${a.telefono}` : ''}</p>
                    </div>
                    {a.plan_activo && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                        {a.plan_activo.clases_restantes} clases
                      </span>
                    )}
                  </label>
                ))
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button type="button" variant="outline" onClick={() => setIsVincularModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isVinculando || !alumnoSeleccionadoId} className="bg-primary-main hover:bg-primary-dark text-white">
              {isVinculando ? 'Vinculando...' : 'Confirmar Vinculación'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal Confirmar Liberar Camilla */}
      <ConfirmModal
        isOpen={!!reservaParaLiberar}
        onClose={() => setReservaParaLiberar(null)}
        onConfirm={handleConfirmarLiberar}
        title="Liberar Camilla Apartada"
        message={`¿Estás seguro de liberar la camilla apartada para ${reservaParaLiberar?.nombre}? El cupo volverá a estar disponible para que cualquier alumna se anote en la web o por WhatsApp.`}
        confirmText={isLiberando ? "Liberando..." : "Sí, Liberar"}
        cancelText="No, Mantener"
        isDestructive={true}
      />

      {/* Modal Cancelar Turno Completo */}
      <ConfirmModal
        isOpen={!!turnoToDelete}
        onClose={() => { setTurnoToDelete(null); setDeleteFuture(false); }}
        onConfirm={handleDeleteTurno}
        title="Cancelar Turno"
        message="¿Estás seguro de cancelar este turno? Las alumnas inscriptas recuperarán su clase."
        confirmText="Sí, Cancelar"
        cancelText="No, Volver"
        isDestructive={true}
      >
        <div className="mb-6 flex items-start gap-2.5 bg-rose-50 p-3.5 rounded-xl border border-rose-200 text-left">
          <input 
            type="checkbox" 
            id="deleteFuture" 
            checked={deleteFuture} 
            onChange={e => setDeleteFuture(e.target.checked)}
            className="mt-0.5 w-4 h-4 text-rose-600 rounded border-rose-300 focus:ring-rose-500 cursor-pointer shrink-0"
          />
          <label htmlFor="deleteFuture" className="text-xs text-rose-900 leading-snug cursor-pointer select-none">
            <strong>Eliminar en serie (todas las futuras):</strong><br />
            Borrar también este mismo horario en todas las semanas futuras. Ideal para eliminar clases fijas canceladas o duplicadas.
          </label>
        </div>
      </ConfirmModal>
    </motion.div>
  );
}
