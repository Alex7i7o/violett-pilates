import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  WalletCards,
  Clock,
  CheckCircle,
  Calendar,
  CalendarClock,
  XCircle,
  Sparkles,
  Plus,
  History,
  X
} from 'lucide-react';

export const ClientDashboard = () => {
  const navigate = useNavigate();
  const [billeteras, setBilleteras] = useState<any[]>([]);
  const [turnos, setTurnos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showHistory, setShowHistory] = useState(false);

  // Modal Cancelar
  const [turnoToCancel, setTurnoToCancel] = useState<any | null>(null);
  const [canceling, setCanceling] = useState(false);

  // Modal Reprogramar
  const [turnoToReschedule, setTurnoToReschedule] = useState<any | null>(null);
  const [newFecha, setNewFecha] = useState('');
  const [newHora, setNewHora] = useState('');
  const [horariosDisponibles, setHorariosDisponibles] = useState<string[]>([]);
  const [loadingHorarios, setLoadingHorarios] = useState(false);
  const [rescheduling, setRescheduling] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [resBill, resTurnos] = await Promise.all([
        api.get('/billeteras/'),
        api.get('/estetica-turnos/')
      ]);
      setBilleteras(resBill.data || []);
      setTurnos(resTurnos.data || []);
    } catch {
      toast.error('Error cargando los datos de tu cuenta');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (turnoToReschedule && newFecha) {
      setLoadingHorarios(true);
      api
        .get(`/disponibilidad/?fecha=${newFecha}&servicio_id=${turnoToReschedule.servicio}&exclude_reserva_id=${turnoToReschedule.id}`)
        .then(res => setHorariosDisponibles(res.data || []))
        .catch(() => toast.error('Error consultando horarios disponibles'))
        .finally(() => setLoadingHorarios(false));
    } else {
      setHorariosDisponibles([]);
    }
  }, [turnoToReschedule, newFecha]);

  const handleConfirmCancel = async () => {
    if (!turnoToCancel) return;
    setCanceling(true);
    try {
      const res = await api.post(`/estetica-turnos/${turnoToCancel.id}/cancelar/`, {
        devolver_credito: true
      });
      if (res.data?.credito_devuelto) {
        toast.success('Turno cancelado. Se reintegró 1 sesión a tu billetera.');
      } else {
        toast.success('Turno cancelado correctamente.');
      }
      setTurnoToCancel(null);
      await fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'No se pudo cancelar el turno.');
    } finally {
      setCanceling(false);
    }
  };

  const handleConfirmReschedule = async () => {
    if (!turnoToReschedule || !newFecha || !newHora) return;
    setRescheduling(true);
    try {
      await api.post(`/estetica-turnos/${turnoToReschedule.id}/reprogramar/`, {
        fecha: newFecha,
        hora_inicio: newHora
      });
      toast.success('¡Turno reprogramado con éxito!');
      setTurnoToReschedule(null);
      setNewFecha('');
      setNewHora('');
      await fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'No se pudo reprogramar el turno.');
    } finally {
      setRescheduling(false);
    }
  };

  const todayStr = new Date().toISOString().split('T')[0];
  const proximosTurnos = turnos.filter(
    t => t.estado === 'CONFIRMADA' && t.fecha >= todayStr
  );
  const historialTurnos = turnos.filter(
    t => !(t.estado === 'CONFIRMADA' && t.fecha >= todayStr)
  );

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', duration: 0.5, bounce: 0.2 } }
  };

  if (loading) {
    return (
      <div className="w-full space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-32 bg-neutral-200 rounded-[2rem] animate-pulse"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="w-full pb-24 space-y-12">
      {/* SECCIÓN 1: MIS PRÓXIMOS TURNOS */}
      <section>
        <div className="flex items-center justify-between gap-3 mb-6 px-2 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary-50 text-primary-main rounded-xl">
              <Calendar size={24} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-neutral-900 tracking-tight">Mis Turnos</h2>
              <p className="text-xs text-neutral-500">Gestioná tus próximas visitas o reprogramá si lo necesitás</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {historialTurnos.length > 0 && (
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="px-3.5 py-2 rounded-xl border border-neutral-200 text-xs font-semibold text-neutral-600 hover:bg-neutral-100 flex items-center gap-1.5 transition-colors"
              >
                <History size={14} />
                {showHistory ? 'Ver próximos' : `Historial (${historialTurnos.length})`}
              </button>
            )}
            <Link
              to="/"
              className="px-4 py-2 rounded-xl bg-primary-main text-white text-xs font-bold hover:bg-primary-hover flex items-center gap-1.5 transition-colors shadow-xs"
            >
              <Plus size={15} /> Nuevo Turno
            </Link>
          </div>
        </div>

        {!showHistory ? (
          proximosTurnos.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-[2rem] p-8 text-center border border-neutral-100 shadow-2xs"
            >
              <p className="text-neutral-600 font-semibold mb-1">No tenés próximos turnos agendados</p>
              <p className="text-xs text-neutral-400 mb-5">Elegí un tratamiento y reservá tu horario en segundos.</p>
              <Link
                to="/"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary-main text-white text-xs font-bold hover:bg-primary-hover transition-colors"
              >
                <Sparkles size={14} /> Reservar un turno ahora
              </Link>
            </motion.div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {proximosTurnos.map(turno => (
                <div
                  key={turno.id}
                  className="bg-white p-6 rounded-[2rem] border border-neutral-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] flex flex-col justify-between gap-4"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Confirmado
                      </span>
                      <span className="text-xs font-medium text-neutral-400">
                        {turno.servicio_detalle?.duracion_minutos || 60} min
                      </span>
                    </div>
                    <h3 className="font-bold text-lg text-neutral-900 mb-2">
                      {turno.servicio_detalle?.nombre || 'Tratamiento Estético'}
                    </h3>
                    <div className="space-y-1 text-sm text-neutral-600">
                      <p className="flex items-center gap-2 font-medium text-neutral-800">
                        <Calendar size={15} className="text-primary-main" />
                        {turno.fecha}
                      </p>
                      <p className="flex items-center gap-2">
                        <Clock size={15} className="text-primary-main" />
                        {String(turno.hora_inicio || '').slice(0, 5)} hs
                        {turno.hora_fin && turno.hora_fin !== '00:00:00' ? ` a ${String(turno.hora_fin).slice(0, 5)} hs` : ''}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-3 border-t border-neutral-100">
                    <button
                      onClick={() => {
                        setTurnoToReschedule(turno);
                        setNewFecha(turno.fecha);
                        setNewHora('');
                      }}
                      className="flex-1 py-2.5 px-3 rounded-xl border border-neutral-200 text-neutral-700 hover:border-primary-main hover:text-primary-main text-xs font-bold flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <CalendarClock size={14} /> Reprogramar
                    </button>
                    <button
                      onClick={() => setTurnoToCancel(turno)}
                      className="py-2.5 px-3 rounded-xl border border-red-100 text-red-600 hover:bg-red-50 text-xs font-bold flex items-center justify-center gap-1.5 transition-colors"
                    >
                      <XCircle size={14} /> Cancelar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {historialTurnos.map(turno => {
              const badgeStyle =
                turno.estado === 'ASISTIO'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : turno.estado === 'CANCELADA'
                  ? 'bg-neutral-100 text-neutral-500 border-neutral-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200';
              return (
                <div
                  key={turno.id}
                  className="bg-white/80 p-5 rounded-2xl border border-neutral-100 flex items-center justify-between gap-4"
                >
                  <div>
                    <h4 className="font-bold text-sm text-neutral-800">
                      {turno.servicio_detalle?.nombre || 'Tratamiento'}
                    </h4>
                    <p className="text-xs text-neutral-500 mt-0.5">
                      {turno.fecha} • {String(turno.hora_inicio || '').slice(0, 5)} hs
                    </p>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase border ${badgeStyle}`}>
                    {turno.estado === 'ASISTIO'
                      ? 'Asistió'
                      : turno.estado === 'NO_ASISTIO'
                      ? 'Ausente'
                      : turno.estado === 'CANCELADA'
                      ? 'Cancelado'
                      : turno.estado}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* SECCIÓN 2: MI BILLETERA */}
      <section>
        <div className="flex items-center justify-between gap-3 mb-6 px-2">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary-50 text-primary-main rounded-xl">
              <WalletCards size={24} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-neutral-900 tracking-tight">Mi Billetera</h2>
              <p className="text-xs text-neutral-500">Tus paquetes de sesiones adquiridos y su saldo disponible</p>
            </div>
          </div>
        </div>

        {billeteras.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-neutral-50 rounded-[2rem] p-8 text-center border-2 border-dashed border-neutral-200"
          >
            <p className="text-neutral-500 font-medium mb-4">No tenés paquetes activos en tu billetera.</p>
            <Link
              to="/tienda-paquetes"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary-main text-white text-xs font-bold hover:bg-primary-hover transition-colors"
            >
              Ir a la Tienda de Paquetes
            </Link>
          </motion.div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid gap-4 sm:grid-cols-2"
          >
            {billeteras.map(bill => {
              const isAgotado = bill.estado === 'AGOTADO' || bill.sesiones_restantes <= 0;
              const isVencido = bill.estado === 'VENCIDO';
              const isInactive = isAgotado || isVencido;
              const progress = bill.sesiones_totales > 0
                ? Math.min(100, (bill.sesiones_restantes / bill.sesiones_totales) * 100)
                : 0;

              return (
                <motion.div
                  variants={itemVariants}
                  key={bill.id}
                  className={`p-6 rounded-[2rem] relative overflow-hidden transition-all flex flex-col justify-between ${
                    isInactive
                      ? 'bg-neutral-100/60 text-neutral-400 border border-neutral-100'
                      : 'bg-white shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-neutral-100 text-neutral-900'
                  }`}
                >
                  <div>
                    <div className="flex justify-between items-start mb-6">
                      <div>
                        <h3 className={`font-bold text-lg leading-tight mb-1 ${isInactive ? 'text-neutral-500' : 'text-neutral-900'}`}>
                          {bill.servicio_detalle?.nombre || 'Servicio'}
                        </h3>
                        <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider">
                          {isVencido ? (
                            <span className="text-red-500 flex items-center gap-1"><Clock size={12} /> Vencido</span>
                          ) : isAgotado ? (
                            <span className="text-orange-500 flex items-center gap-1"><CheckCircle size={12} /> Agotado</span>
                          ) : (
                            <span className="text-green-600 flex items-center gap-1"><CheckCircle size={12} /> Activo</span>
                          )}
                        </div>
                      </div>

                      {!isInactive && (
                        <button
                          onClick={() => navigate(`/?servicio_id=${bill.servicio}`)}
                          className="px-3.5 py-1.5 rounded-full bg-primary-50 text-primary-main hover:bg-primary-main hover:text-white text-xs font-bold transition-colors"
                        >
                          Agendar turno
                        </button>
                      )}
                    </div>

                    <div className="mb-6">
                      <div className="flex justify-between text-sm mb-2 font-medium">
                        <span className={isInactive ? 'text-neutral-400' : 'text-neutral-600'}>
                          <strong className={`text-lg ${isInactive ? '' : 'text-primary-main'}`}>{bill.sesiones_restantes}</strong> restantes
                        </span>
                        <span className="text-neutral-400 self-end mb-0.5">de {bill.sesiones_totales} totales</span>
                      </div>
                      <div className="w-full bg-neutral-100 rounded-full h-2.5 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${progress}%` }}
                          transition={{ duration: 0.8 }}
                          className={`h-full rounded-full ${isInactive ? 'bg-neutral-300' : 'bg-primary-main'}`}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-between text-[11px] font-medium text-neutral-400 bg-neutral-50 p-3 rounded-xl">
                    <div>
                      <p className="uppercase tracking-wider text-[9px] mb-0.5 opacity-70">Compra</p>
                      <p>{bill.fecha_compra}</p>
                    </div>
                    <div className="text-right">
                      <p className="uppercase tracking-wider text-[9px] mb-0.5 opacity-70">Vence</p>
                      <p>{bill.fecha_vencimiento}</p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </section>

      {/* MODAL REPROGRAMAR */}
      <AnimatePresence>
        {turnoToReschedule && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-5"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-neutral-900">Reprogramar Turno</h3>
                <button onClick={() => setTurnoToReschedule(null)} className="p-1 text-neutral-400 hover:text-neutral-700">
                  <X size={20} />
                </button>
              </div>

              <div className="p-3.5 rounded-2xl bg-neutral-50 border border-neutral-100 text-xs text-neutral-600">
                <p className="font-bold text-neutral-900 text-sm">{turnoToReschedule.servicio_detalle?.nombre}</p>
                <p>Turno actual: {turnoToReschedule.fecha} a las {String(turnoToReschedule.hora_inicio || '').slice(0, 5)} hs</p>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-neutral-500 mb-1.5">Nueva Fecha</label>
                <input
                  type="date"
                  min={todayStr}
                  value={newFecha}
                  onChange={e => {
                    setNewFecha(e.target.value);
                    setNewHora('');
                  }}
                  className="w-full p-3 rounded-xl border border-neutral-200 font-medium text-sm"
                />
              </div>

              {newFecha && (
                <div>
                  <label className="block text-xs font-bold uppercase text-neutral-500 mb-2">Nuevo Horario</label>
                  {loadingHorarios ? (
                    <p className="text-xs text-neutral-500 py-2">Consultando disponibilidad...</p>
                  ) : horariosDisponibles.length === 0 ? (
                    <p className="text-xs text-neutral-500 py-2">No hay horarios libres en esta fecha.</p>
                  ) : (
                    <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                      {horariosDisponibles.map(h => (
                        <button
                          key={h}
                          type="button"
                          onClick={() => setNewHora(h)}
                          className={`px-3.5 py-2 rounded-xl text-xs font-bold border transition-all ${
                            newHora === h
                              ? 'bg-primary-main text-white border-primary-main'
                              : 'border-neutral-200 text-neutral-700 hover:border-primary-main'
                          }`}
                        >
                          {h} hs
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setTurnoToReschedule(null)}
                  className="flex-1 py-3 rounded-xl border border-neutral-200 text-xs font-bold text-neutral-600 hover:bg-neutral-50"
                >
                  Volver
                </button>
                <button
                  type="button"
                  disabled={!newFecha || !newHora || rescheduling}
                  onClick={handleConfirmReschedule}
                  className="flex-1 py-3 rounded-xl bg-primary-main text-white text-xs font-bold hover:bg-primary-hover disabled:opacity-50"
                >
                  {rescheduling ? 'Guardando...' : 'Confirmar Cambio'}
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
              className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-5"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-neutral-900">¿Cancelar este turno?</h3>
                <button onClick={() => setTurnoToCancel(null)} className="p-1 text-neutral-400 hover:text-neutral-700">
                  <X size={20} />
                </button>
              </div>

              <p className="text-sm text-neutral-600">
                Estás por cancelar tu turno de <strong>{turnoToCancel.servicio_detalle?.nombre}</strong> del día{' '}
                <strong>{turnoToCancel.fecha}</strong> a las <strong>{String(turnoToCancel.hora_inicio || '').slice(0, 5)} hs</strong>.
                La sesión será reintegrada automáticamente a tu billetera.
              </p>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setTurnoToCancel(null)}
                  className="flex-1 py-3 rounded-xl border border-neutral-200 text-xs font-bold text-neutral-600 hover:bg-neutral-50"
                >
                  No, mantener turno
                </button>
                <button
                  type="button"
                  disabled={canceling}
                  onClick={handleConfirmCancel}
                  className="flex-1 py-3 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 disabled:opacity-50"
                >
                  {canceling ? 'Cancelando...' : 'Sí, cancelar turno'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
