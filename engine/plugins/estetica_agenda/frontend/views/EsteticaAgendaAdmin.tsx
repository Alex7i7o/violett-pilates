import React, { useState, useEffect, useMemo } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Calendar,
  Clock,
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  UserCheck,
  UserX,
  CalendarClock,
  ChevronLeft,
  ChevronRight,
  MessageCircle,
  Sparkles,
  WalletCards,
  X
} from 'lucide-react';

export const EsteticaAgendaAdmin = () => {
  const todayStr = new Date().toISOString().split('T')[0];

  const [activeTab, setActiveTab] = useState<'dia' | 'todos'>('dia');
  const [selectedDate, setSelectedDate] = useState<string>(todayStr);

  const [turnos, setTurnos] = useState<any[]>([]);
  const [servicios, setServicios] = useState<any[]>([]);
  const [pacientes, setPacientes] = useState<any[]>([]);
  const [billeteras, setBilleteras] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filtros en pestaña "Todos"
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('TODOS');
  const [servicioFilter, setServicioFilter] = useState('TODOS');

  // Modal Nuevo Turno Manual
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [newUsuarioId, setNewUsuarioId] = useState('');
  const [pacienteSearch, setPacienteSearch] = useState('');
  const [newServicioId, setNewServicioId] = useState('');
  const [newFecha, setNewFecha] = useState(todayStr);
  const [newHora, setNewHora] = useState('');
  const [newDescontarCredito, setNewDescontarCredito] = useState(true);
  const [slotsDisponibles, setSlotsDisponibles] = useState<string[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submittingNew, setSubmittingNew] = useState(false);

  // Modal Reprogramar
  const [turnoToReschedule, setTurnoToReschedule] = useState<any | null>(null);
  const [rescheduleFecha, setRescheduleFecha] = useState('');
  const [rescheduleHora, setRescheduleHora] = useState('');
  const [rescheduleSlots, setRescheduleSlots] = useState<string[]>([]);
  const [submittingReschedule, setSubmittingReschedule] = useState(false);

  // Modal Cancelar
  const [turnoToCancel, setTurnoToCancel] = useState<any | null>(null);
  const [devolverCreditoCancel, setDevolverCreditoCancel] = useState(true);
  const [submittingCancel, setSubmittingCancel] = useState(false);

  const fetchAll = async () => {
    try {
      setLoading(true);
      const [resTurnos, resServicios, resPacientes, resBilleteras] = await Promise.all([
        api.get('/estetica-turnos/'),
        api.get('/servicios/'),
        api.get('/admin/alumnos/').catch(() => ({ data: [] })),
        api.get('/billeteras/').catch(() => ({ data: [] }))
      ]);
      setTurnos(resTurnos.data || []);
      setServicios(resServicios.data || []);
      setPacientes(resPacientes.data || []);
      setBilleteras(resBilleteras.data || []);
    } catch {
      toast.error('Error al cargar la agenda de estética');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  // Cargar horarios disponibles para Nuevo Turno Manual
  useEffect(() => {
    if (isNewModalOpen && newFecha && newServicioId) {
      setLoadingSlots(true);
      api
        .get(`/disponibilidad/?fecha=${newFecha}&servicio_id=${newServicioId}`)
        .then(res => setSlotsDisponibles(res.data || []))
        .catch(() => setSlotsDisponibles([]))
        .finally(() => setLoadingSlots(false));
    } else {
      setSlotsDisponibles([]);
    }
  }, [isNewModalOpen, newFecha, newServicioId]);

  // Cargar horarios disponibles para Reprogramar
  useEffect(() => {
    if (turnoToReschedule && rescheduleFecha) {
      api
        .get(`/disponibilidad/?fecha=${rescheduleFecha}&servicio_id=${turnoToReschedule.servicio}&exclude_reserva_id=${turnoToReschedule.id}`)
        .then(res => setRescheduleSlots(res.data || []))
        .catch(() => setRescheduleSlots([]));
    } else {
      setRescheduleSlots([]);
    }
  }, [turnoToReschedule, rescheduleFecha]);

  const shiftDate = (days: number) => {
    const [y, m, d] = selectedDate.split('-').map(Number);
    const dt = new Date(y, m - 1, d + days);
    const yyyy = dt.getFullYear();
    const mm = String(dt.getMonth() + 1).padStart(2, '0');
    const dd = String(dt.getDate()).padStart(2, '0');
    setSelectedDate(`${yyyy}-${mm}-${dd}`);
  };

  const handleStatusChange = async (turnoId: string, nuevoEstado: string) => {
    try {
      await api.patch(`/estetica-turnos/${turnoId}/`, { estado: nuevoEstado });
      toast.success(
        nuevoEstado === 'ASISTIO'
          ? 'Marcado como Asistió'
          : nuevoEstado === 'NO_ASISTIO'
          ? 'Marcado como Ausente'
          : 'Estado actualizado'
      );
      await fetchAll();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error al actualizar estado');
    }
  };

  const handleCreateManual = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsuarioId || !newServicioId || !newFecha || !newHora) {
      toast.error('Completá paciente, servicio, fecha y horario.');
      return;
    }
    setSubmittingNew(true);
    try {
      await api.post('/estetica-turnos/', {
        usuario: newUsuarioId,
        usuario_id: newUsuarioId,
        servicio: newServicioId,
        fecha: newFecha,
        hora_inicio: newHora,
        descontar_credito: newDescontarCredito
      });
      toast.success('Turno agendado correctamente');
      setIsNewModalOpen(false);
      setNewHora('');
      await fetchAll();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'No se pudo agendar el turno');
    } finally {
      setSubmittingNew(false);
    }
  };

  const handleRescheduleConfirm = async () => {
    if (!turnoToReschedule || !rescheduleFecha || !rescheduleHora) return;
    setSubmittingReschedule(true);
    try {
      await api.post(`/estetica-turnos/${turnoToReschedule.id}/reprogramar/`, {
        fecha: rescheduleFecha,
        hora_inicio: rescheduleHora
      });
      toast.success('Turno reprogramado con éxito');
      setTurnoToReschedule(null);
      await fetchAll();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'No se pudo reprogramar');
    } finally {
      setSubmittingReschedule(false);
    }
  };

  const handleCancelConfirm = async () => {
    if (!turnoToCancel) return;
    setSubmittingCancel(true);
    try {
      const res = await api.post(`/estetica-turnos/${turnoToCancel.id}/cancelar/`, {
        devolver_credito: devolverCreditoCancel
      });
      if (res.data?.credito_devuelto) {
        toast.success('Turno cancelado y sesión reintegrada a la billetera');
      } else {
        toast.success('Turno cancelado');
      }
      setTurnoToCancel(null);
      await fetchAll();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'No se pudo cancelar el turno');
    } finally {
      setSubmittingCancel(false);
    }
  };

  const turnosDelDia = useMemo(
    () => turnos.filter(t => t.fecha === selectedDate),
    [turnos, selectedDate]
  );

  const turnosFiltrados = useMemo(() => {
    return turnos.filter(t => {
      if (statusFilter !== 'TODOS' && t.estado !== statusFilter) return false;
      if (servicioFilter !== 'TODOS' && String(t.servicio) !== String(servicioFilter)) return false;
      if (searchTerm.trim()) {
        const q = searchTerm.toLowerCase();
        const nombreCompleto = `${t.usuario_detalle?.nombre || ''} ${t.usuario_detalle?.apellido || ''}`.toLowerCase();
        const email = (t.usuario_detalle?.email || '').toLowerCase();
        const tel = (t.usuario_detalle?.telefono || '').toLowerCase();
        const srv = (t.servicio_detalle?.nombre || '').toLowerCase();
        if (!nombreCompleto.includes(q) && !email.includes(q) && !tel.includes(q) && !srv.includes(q)) {
          return false;
        }
      }
      return true;
    });
  }, [turnos, statusFilter, servicioFilter, searchTerm]);

  const kpisDia = useMemo(() => {
    return {
      total: turnosDelDia.filter(t => t.estado !== 'CANCELADA').length,
      confirmados: turnosDelDia.filter(t => t.estado === 'CONFIRMADA').length,
      asistieron: turnosDelDia.filter(t => t.estado === 'ASISTIO').length,
      ausentes: turnosDelDia.filter(t => t.estado === 'NO_ASISTIO').length
    };
  }, [turnosDelDia]);

  const sesionesPacienteSeleccionado = useMemo(() => {
    if (!newUsuarioId || !newServicioId) return 0;
    return billeteras
      .filter(
        b =>
          String(b.usuario) === String(newUsuarioId) &&
          String(b.servicio) === String(newServicioId) &&
          b.estado === 'ACTIVO' &&
          b.sesiones_restantes > 0
      )
      .reduce((acc, b) => acc + Number(b.sesiones_restantes || 0), 0);
  }, [billeteras, newUsuarioId, newServicioId]);

  const pacientesFiltradosModal = useMemo(() => {
    if (!pacienteSearch.trim()) return pacientes;
    const q = pacienteSearch.toLowerCase();
    return pacientes.filter((p: any) => {
      const full = `${p.nombre || ''} ${p.apellido || ''} ${p.email || ''} ${p.telefono || ''}`.toLowerCase();
      return full.includes(q);
    });
  }, [pacientes, pacienteSearch]);

  const getBadgeEstado = (estado: string) => {
    switch (estado) {
      case 'CONFIRMADA':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'ASISTIO':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'NO_ASISTIO':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'CANCELADA':
        return 'bg-neutral-100 text-neutral-500 border-neutral-200';
      default:
        return 'bg-neutral-100 text-neutral-600 border-neutral-200';
    }
  };

  const getLabelEstado = (estado: string) => {
    switch (estado) {
      case 'CONFIRMADA':
        return 'Confirmado';
      case 'ASISTIO':
        return 'Asistió';
      case 'NO_ASISTIO':
        return 'Ausente';
      case 'CANCELADA':
        return 'Cancelado';
      default:
        return estado;
    }
  };

  const listaActiva = activeTab === 'dia' ? turnosDelDia : turnosFiltrados;

  return (
    <div className="space-y-6 pb-16">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 tracking-tight">Agenda de Turnos</h1>
          <p className="text-sm text-neutral-500">Gestión de sesiones estéticas, asistencia y carga manual de turnos</p>
        </div>

        <button
          onClick={() => {
            setNewFecha(selectedDate);
            if (servicios.length > 0 && !newServicioId) setNewServicioId(servicios[0].id);
            setIsNewModalOpen(true);
          }}
          className="px-5 py-3 rounded-2xl bg-primary-main text-white font-bold text-sm hover:bg-primary-hover transition-colors flex items-center justify-center gap-2 shadow-sm"
        >
          <Plus size={18} /> Agendar Turno Manual
        </button>
      </div>

      {/* TABS */}
      <div className="flex items-center gap-2 border-b border-neutral-200 pb-3">
        <button
          onClick={() => setActiveTab('dia')}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'dia'
              ? 'bg-primary-main text-white shadow-xs'
              : 'text-neutral-600 hover:bg-neutral-100'
          }`}
        >
          Turnos del Día
        </button>
        <button
          onClick={() => setActiveTab('todos')}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'todos'
              ? 'bg-primary-main text-white shadow-xs'
              : 'text-neutral-600 hover:bg-neutral-100'
          }`}
        >
          Todos los Turnos ({turnos.length})
        </button>
      </div>

      {/* CONTROLES SEGÚN PESTAÑA */}
      {activeTab === 'dia' ? (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-2xl border border-neutral-200 flex flex-wrap items-center justify-between gap-4 shadow-2xs">
            <div className="flex items-center gap-2">
              <button
                onClick={() => shiftDate(-1)}
                className="p-2 rounded-xl border border-neutral-200 hover:bg-neutral-50 text-neutral-700"
                title="Día anterior"
              >
                <ChevronLeft size={18} />
              </button>
              <input
                type="date"
                value={selectedDate}
                onChange={e => setSelectedDate(e.target.value)}
                className="px-3.5 py-2 rounded-xl border border-neutral-200 font-bold text-sm text-neutral-900"
              />
              <button
                onClick={() => shiftDate(1)}
                className="p-2 rounded-xl border border-neutral-200 hover:bg-neutral-50 text-neutral-700"
                title="Día siguiente"
              >
                <ChevronRight size={18} />
              </button>
              {selectedDate !== todayStr && (
                <button
                  onClick={() => setSelectedDate(todayStr)}
                  className="px-3 py-2 rounded-xl bg-primary-50 text-primary-main text-xs font-bold hover:bg-primary-100 transition-colors"
                >
                  Hoy
                </button>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs font-bold">
              <span className="px-3 py-1.5 rounded-xl bg-neutral-100 text-neutral-700">
                Activos: {kpisDia.total}
              </span>
              <span className="px-3 py-1.5 rounded-xl bg-blue-50 text-blue-700">
                Confirmados: {kpisDia.confirmados}
              </span>
              <span className="px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700">
                Asistieron: {kpisDia.asistieron}
              </span>
              <span className="px-3 py-1.5 rounded-xl bg-amber-50 text-amber-700">
                Ausentes: {kpisDia.ausentes}
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white p-4 rounded-2xl border border-neutral-200 grid grid-cols-1 sm:grid-cols-3 gap-3 shadow-2xs">
          <div className="relative">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
            <input
              type="text"
              placeholder="Buscar paciente o servicio..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-neutral-200 text-sm"
            />
          </div>
          <select
            value={servicioFilter}
            onChange={e => setServicioFilter(e.target.value)}
            className="p-2.5 rounded-xl border border-neutral-200 text-sm bg-white"
          >
            <option value="TODOS">Todos los tratamientos</option>
            {servicios.map(s => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="p-2.5 rounded-xl border border-neutral-200 text-sm bg-white"
          >
            <option value="TODOS">Todos los estados</option>
            <option value="CONFIRMADA">Confirmados</option>
            <option value="ASISTIO">Asistió</option>
            <option value="NO_ASISTIO">Ausente</option>
            <option value="CANCELADA">Cancelados</option>
          </select>
        </div>
      )}

      {/* LISTA DE TURNOS */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-neutral-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : listaActiva.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center border border-neutral-200">
          <Calendar className="mx-auto text-neutral-300 mb-3" size={36} />
          <p className="text-neutral-700 font-bold">
            {activeTab === 'dia'
              ? 'No hay turnos registrados para esta fecha'
              : 'No se encontraron turnos con esos filtros'}
          </p>
          <p className="text-xs text-neutral-400 mt-1">
            Podés agendar un turno manualmente usando el botón superior.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {listaActiva.map(turno => {
            const pac = turno.usuario_detalle || {};
            const srv = turno.servicio_detalle || {};
            const nombrePaciente =
              `${pac.nombre || ''} ${pac.apellido || ''}`.trim() || pac.email || 'Paciente';
            const cleanPhone = String(pac.telefono || '').replace(/\D/g, '');

            return (
              <div
                key={turno.id}
                className={`bg-white p-4 sm:p-5 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                  turno.estado === 'CANCELADA'
                    ? 'border-neutral-100 opacity-60'
                    : 'border-neutral-200 shadow-2xs'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="px-3.5 py-2.5 rounded-2xl bg-primary-50 text-primary-main text-center min-w-[84px] shrink-0">
                    <p className="text-sm font-black leading-none">
                      {String(turno.hora_inicio || '').slice(0, 5)}
                    </p>
                    {turno.hora_fin && turno.hora_fin !== '00:00:00' && (
                      <p className="text-[10px] font-semibold opacity-75 mt-1">
                        a {String(turno.hora_fin).slice(0, 5)}
                      </p>
                    )}
                  </div>

                  <div>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="font-bold text-base text-neutral-900">{nombrePaciente}</span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${getBadgeEstado(
                          turno.estado
                        )}`}
                      >
                        {getLabelEstado(turno.estado)}
                      </span>
                      {activeTab === 'todos' && (
                        <span className="text-xs font-semibold text-neutral-500 bg-neutral-100 px-2.5 py-0.5 rounded-lg">
                          {turno.fecha}
                        </span>
                      )}
                    </div>

                    <p className="text-sm font-semibold text-primary-main flex items-center gap-1.5">
                      <Sparkles size={14} /> {srv.nombre || 'Tratamiento'} ({srv.duracion_minutos || 60} min)
                    </p>

                    <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-neutral-500">
                      {pac.email && <span>{pac.email}</span>}
                      {cleanPhone && (
                        <a
                          href={`https://wa.me/${cleanPhone}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-emerald-600 hover:underline font-semibold flex items-center gap-1"
                        >
                          <MessageCircle size={13} /> {pac.telefono}
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                {/* ACCIONES */}
                {turno.estado !== 'CANCELADA' && (
                  <div className="flex flex-wrap items-center gap-2 pt-3 md:pt-0 border-t md:border-t-0 border-neutral-100">
                    <button
                      onClick={() => handleStatusChange(turno.id, 'ASISTIO')}
                      className={`px-3 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 border transition-colors ${
                        turno.estado === 'ASISTIO'
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                      }`}
                      title="Marcar asistencia"
                    >
                      <UserCheck size={14} /> Asistió
                    </button>

                    <button
                      onClick={() => handleStatusChange(turno.id, 'NO_ASISTIO')}
                      className={`px-3 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 border transition-colors ${
                        turno.estado === 'NO_ASISTIO'
                          ? 'bg-amber-500 text-white border-amber-500'
                          : 'border-amber-200 text-amber-700 hover:bg-amber-50'
                      }`}
                      title="Marcar ausencia"
                    >
                      <UserX size={14} /> Ausente
                    </button>

                    <button
                      onClick={() => {
                        setTurnoToReschedule(turno);
                        setRescheduleFecha(turno.fecha);
                        setRescheduleHora(String(turno.hora_inicio || '').slice(0, 5));
                      }}
                      className="px-3 py-2 rounded-xl text-xs font-bold border border-neutral-200 text-neutral-700 hover:bg-neutral-50 flex items-center gap-1.5"
                    >
                      <CalendarClock size={14} /> Reprogramar
                    </button>

                    <button
                      onClick={() => {
                        setTurnoToCancel(turno);
                        setDevolverCreditoCancel(true);
                      }}
                      className="px-3 py-2 rounded-xl text-xs font-bold border border-red-200 text-red-600 hover:bg-red-50 flex items-center gap-1.5"
                    >
                      <XCircle size={14} /> Cancelar
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* MODAL NUEVO TURNO MANUAL */}
      <AnimatePresence>
        {isNewModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.form
              onSubmit={handleCreateManual}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-neutral-900">Agendar Turno Manual</h3>
                <button
                  type="button"
                  onClick={() => setIsNewModalOpen(false)}
                  className="p-1 text-neutral-400 hover:text-neutral-700"
                >
                  <X size={20} />
                </button>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-neutral-500 mb-1">
                  Buscar / Seleccionar Paciente
                </label>
                <input
                  type="text"
                  placeholder="Filtrar por nombre o email..."
                  value={pacienteSearch}
                  onChange={e => setPacienteSearch(e.target.value)}
                  className="w-full p-2.5 mb-2 rounded-xl border border-neutral-200 text-xs"
                />
                <select
                  required
                  value={newUsuarioId}
                  onChange={e => setNewUsuarioId(e.target.value)}
                  className="w-full p-3 rounded-xl border border-neutral-200 text-sm bg-white font-medium"
                >
                  <option value="">Seleccionar paciente...</option>
                  {pacientesFiltradosModal.map((p: any) => (
                    <option key={p.id} value={p.id}>
                      {`${p.nombre || ''} ${p.apellido || ''}`.trim() || p.email} ({p.email})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-neutral-500 mb-1">
                  Tratamiento
                </label>
                <select
                  required
                  value={newServicioId}
                  onChange={e => {
                    setNewServicioId(e.target.value);
                    setNewHora('');
                  }}
                  className="w-full p-3 rounded-xl border border-neutral-200 text-sm bg-white font-medium"
                >
                  <option value="">Seleccionar tratamiento...</option>
                  {servicios.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.nombre} ({s.duracion_minutos} min)
                    </option>
                  ))}
                </select>
              </div>

              {newUsuarioId && newServicioId && (
                <div className="p-3 rounded-xl bg-neutral-50 border border-neutral-200 flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-neutral-600 font-medium">
                    <WalletCards size={15} className="text-primary-main" />
                    Sesiones activas del paciente en este servicio:
                  </span>
                  <strong className={sesionesPacienteSeleccionado > 0 ? 'text-emerald-600' : 'text-amber-600'}>
                    {sesionesPacienteSeleccionado} disponibles
                  </strong>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold uppercase text-neutral-500 mb-1">Fecha</label>
                  <input
                    type="date"
                    required
                    value={newFecha}
                    onChange={e => setNewFecha(e.target.value)}
                    className="w-full p-3 rounded-xl border border-neutral-200 text-sm font-medium"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-neutral-500 mb-1">
                    Hora de Inicio
                  </label>
                  <input
                    type="time"
                    required
                    value={newHora}
                    onChange={e => setNewHora(e.target.value)}
                    className="w-full p-3 rounded-xl border border-neutral-200 text-sm font-medium"
                  />
                </div>
              </div>

              {newFecha && newServicioId && (
                <div>
                  <p className="text-[11px] font-bold uppercase text-neutral-400 mb-1.5">
                    Horarios sugeridos según disponibilidad:
                  </p>
                  {loadingSlots ? (
                    <p className="text-xs text-neutral-400">Calculando horarios libres...</p>
                  ) : slotsDisponibles.length === 0 ? (
                    <p className="text-xs text-neutral-400">
                      Sin horarios libres automáticos (podés ingresar una hora manual arriba).
                    </p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto">
                      {slotsDisponibles.map(slot => (
                        <button
                          key={slot}
                          type="button"
                          onClick={() => setNewHora(slot)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${
                            newHora === slot
                              ? 'bg-primary-main text-white border-primary-main'
                              : 'border-neutral-200 text-neutral-700 hover:border-primary-main'
                          }`}
                        >
                          {slot}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <label className="flex items-center gap-2.5 p-3 rounded-xl bg-primary-50/50 border border-primary-100 cursor-pointer text-xs font-semibold text-neutral-800">
                <input
                  type="checkbox"
                  checked={newDescontarCredito}
                  onChange={e => setNewDescontarCredito(e.target.checked)}
                  className="rounded text-primary-main"
                />
                Descontar 1 sesión de la billetera del paciente
              </label>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsNewModalOpen(false)}
                  className="flex-1 py-3 rounded-xl border border-neutral-200 text-xs font-bold text-neutral-600 hover:bg-neutral-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={submittingNew}
                  className="flex-1 py-3 rounded-xl bg-primary-main text-white text-xs font-bold hover:bg-primary-hover disabled:opacity-50"
                >
                  {submittingNew ? 'Guardando...' : 'Confirmar Turno'}
                </button>
              </div>
            </motion.form>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL REPROGRAMAR */}
      <AnimatePresence>
        {turnoToReschedule && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-neutral-900">Reprogramar Turno</h3>
                <button
                  onClick={() => setTurnoToReschedule(null)}
                  className="p-1 text-neutral-400 hover:text-neutral-700"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold uppercase text-neutral-500 mb-1">Nueva Fecha</label>
                  <input
                    type="date"
                    value={rescheduleFecha}
                    onChange={e => setRescheduleFecha(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-neutral-200 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase text-neutral-500 mb-1">Nueva Hora</label>
                  <input
                    type="time"
                    value={rescheduleHora}
                    onChange={e => setRescheduleHora(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-neutral-200 text-sm"
                  />
                </div>
              </div>

              {rescheduleSlots.length > 0 && (
                <div>
                  <p className="text-[11px] font-bold uppercase text-neutral-400 mb-1.5">Horarios disponibles:</p>
                  <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                    {rescheduleSlots.map(s => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setRescheduleHora(s)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${
                          rescheduleHora === s
                            ? 'bg-primary-main text-white border-primary-main'
                            : 'border-neutral-200 text-neutral-700'
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setTurnoToReschedule(null)}
                  className="flex-1 py-3 rounded-xl border border-neutral-200 text-xs font-bold text-neutral-600"
                >
                  Cerrar
                </button>
                <button
                  type="button"
                  disabled={submittingReschedule || !rescheduleFecha || !rescheduleHora}
                  onClick={handleRescheduleConfirm}
                  className="flex-1 py-3 rounded-xl bg-primary-main text-white text-xs font-bold disabled:opacity-50"
                >
                  {submittingReschedule ? 'Guardando...' : 'Guardar Cambios'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL CANCELAR */}
      <AnimatePresence>
        {turnoToCancel && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-neutral-900">Cancelar Turno</h3>
                <button
                  onClick={() => setTurnoToCancel(null)}
                  className="p-1 text-neutral-400 hover:text-neutral-700"
                >
                  <X size={20} />
                </button>
              </div>

              <p className="text-sm text-neutral-600">
                ¿Confirmás la cancelación del turno de{' '}
                <strong>{turnoToCancel.servicio_detalle?.nombre}</strong> del día{' '}
                <strong>{turnoToCancel.fecha}</strong> ({String(turnoToCancel.hora_inicio || '').slice(0, 5)} hs)?
              </p>

              <label className="flex items-center gap-2.5 p-3 rounded-xl bg-neutral-50 border border-neutral-200 cursor-pointer text-xs font-semibold text-neutral-800">
                <input
                  type="checkbox"
                  checked={devolverCreditoCancel}
                  onChange={e => setDevolverCreditoCancel(e.target.checked)}
                  className="rounded text-primary-main"
                />
                Reintegrar 1 sesión a la billetera del paciente
              </label>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setTurnoToCancel(null)}
                  className="flex-1 py-3 rounded-xl border border-neutral-200 text-xs font-bold text-neutral-600"
                >
                  Volver
                </button>
                <button
                  type="button"
                  disabled={submittingCancel}
                  onClick={handleCancelConfirm}
                  className="flex-1 py-3 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 disabled:opacity-50"
                >
                  {submittingCancel ? 'Cancelando...' : 'Confirmar Cancelación'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
