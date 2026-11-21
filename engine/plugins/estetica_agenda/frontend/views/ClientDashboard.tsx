import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Badge,
  Button,
  Modal,
  ConfirmModal,
  EmptyState,
  DatePicker,
  haptics
} from 'fireseed-ui';
import {
  WalletCards,
  Clock,
  CheckCircle,
  Calendar,
  CalendarClock,
  XCircle,
  Sparkles,
  Plus,
  History
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
        toast.success('Turno cancelado exitosamente.');
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
          <div key={i} className="h-32 bg-white rounded-2xl border border-neutral-100 shadow-soft animate-pulse"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="w-full pb-24 space-y-12">
      {/* SECCIÓN 1: MIS PRÓXIMOS TURNOS */}
      <section>
        <div className="flex items-center justify-between gap-3 mb-6 px-1 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-[#F9F6ED] border border-[#C5A059]/30 text-[#C5A059] rounded-xl shadow-xs">
              <Calendar size={22} />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-[#34236F] font-serif tracking-tight">Mis Turnos</h2>
              <p className="text-xs text-neutral-500">Gestioná tus próximas visitas o reprogramá si lo necesitás</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {historialTurnos.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  haptics.light();
                  setShowHistory(!showHistory);
                }}
                className="text-xs border-neutral-200 text-[#34236F] hover:bg-neutral-50 rounded-xl"
              >
                <History size={13} className="mr-1.5" />
                {showHistory ? 'Ver próximos' : `Historial (${historialTurnos.length})`}
              </Button>
            )}
            <Link to="/">
              <Button
                variant="glow"
                size="sm"
                onClick={() => haptics.light()}
                className="text-xs !bg-[#C5A059] !text-white hover:!bg-[#B38E4C] font-bold rounded-xl"
              >
                <Plus size={14} className="mr-1" /> Nuevo Turno
              </Button>
            </Link>
          </div>
        </div>

        {!showHistory ? (
          proximosTurnos.length === 0 ? (
            <div className="bg-white rounded-2xl p-8 text-center border border-neutral-100 shadow-soft">
              <p className="text-neutral-700 font-semibold mb-1">No tenés próximos turnos agendados</p>
              <p className="text-xs text-neutral-400 mb-5">Elegí un tratamiento y reservá tu horario en segundos.</p>
              <Link to="/">
                <Button variant="glow" size="md" className="!bg-[#C5A059] !text-white hover:!bg-[#B38E4C] font-bold text-xs rounded-xl">
                  <Sparkles size={14} className="mr-1.5" /> Reservar un turno ahora
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {proximosTurnos.map(turno => (
                <div
                  key={turno.id}
                  className="bg-white border border-neutral-100 shadow-soft p-6 rounded-2xl flex flex-col justify-between gap-4"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Confirmado
                      </span>
                      <span className="text-xs font-mono text-neutral-400">
                        {turno.servicio_detalle?.duracion_minutos || 60} min
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-[#34236F] font-serif mb-2">
                      {turno.servicio_detalle?.nombre || 'Tratamiento Estético'}
                    </h3>
                    <div className="space-y-1.5 text-xs text-neutral-600">
                      <p className="flex items-center gap-2 font-medium text-[#34236F]">
                        <Calendar size={14} className="text-[#C5A059]" />
                        {turno.fecha}
                      </p>
                      <p className="flex items-center gap-2">
                        <Clock size={14} className="text-[#C5A059]" />
                        {String(turno.hora_inicio || '').slice(0, 5)} hs
                        {turno.hora_fin && turno.hora_fin !== '00:00:00' ? ` a ${String(turno.hora_fin).slice(0, 5)} hs` : ''}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-3 border-t border-neutral-100">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        haptics.light();
                        setTurnoToReschedule(turno);
                        setNewFecha(turno.fecha);
                        setNewHora('');
                      }}
                      className="flex-1 text-xs border-neutral-200 text-[#34236F] hover:border-[#C5A059] rounded-xl"
                    >
                      <CalendarClock size={13} className="mr-1.5" /> Reprogramar
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        haptics.warning();
                        setTurnoToCancel(turno);
                      }}
                      className="text-xs text-rose-500 hover:text-rose-600 hover:bg-rose-50 rounded-xl"
                    >
                      <XCircle size={13} className="mr-1" /> Cancelar
                    </Button>
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
                  className="bg-white border border-neutral-100 p-5 rounded-2xl flex items-center justify-between gap-4 shadow-2xs"
                >
                  <div>
                    <h4 className="font-bold text-sm text-[#34236F] font-serif">
                      {turno.servicio_detalle?.nombre || 'Tratamiento'}
                    </h4>
                    <p className="text-xs text-neutral-400 mt-0.5 font-mono">
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
        <div className="flex items-center justify-between gap-3 mb-6 px-1">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-[#F9F6ED] border border-[#C5A059]/30 text-[#C5A059] rounded-xl shadow-xs">
              <WalletCards size={22} />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-[#34236F] font-serif tracking-tight">Mi Billetera</h2>
              <p className="text-xs text-neutral-500">Tus paquetes de sesiones adquiridos y su saldo disponible</p>
            </div>
          </div>
        </div>

        {billeteras.length === 0 ? (
          <div className="bg-white border border-neutral-100 rounded-2xl p-8 text-center shadow-soft">
            <p className="text-neutral-600 font-semibold mb-1">No tenés paquetes activos en tu billetera</p>
            <p className="text-xs text-neutral-400 mb-5">Adquirí sesiones con descuento en la tienda y usalas cuando quieras.</p>
            <Link to="/tienda">
              <Button variant="glow" size="md" className="!bg-[#C5A059] !text-white hover:!bg-[#B38E4C] font-bold text-xs rounded-xl">
                Ir a la Tienda de Paquetes
              </Button>
            </Link>
          </div>
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
                  className={`p-6 rounded-2xl relative overflow-hidden transition-all flex flex-col justify-between border ${
                    isInactive
                      ? 'bg-neutral-50 text-neutral-400 border-neutral-200'
                      : 'bg-white shadow-soft border-neutral-100 text-[#34236F]'
                  }`}
                >
                  <div>
                    <div className="flex justify-between items-start mb-5">
                      <div>
                        <h3 className={`font-bold text-lg leading-tight mb-1 font-serif ${isInactive ? 'text-neutral-400' : 'text-[#34236F]'}`}>
                          {bill.servicio_detalle?.nombre || 'Servicio'}
                        </h3>
                        <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider">
                          {isVencido ? (
                            <span className="text-rose-500 flex items-center gap-1"><Clock size={11} /> Vencido</span>
                          ) : isAgotado ? (
                            <span className="text-amber-500 flex items-center gap-1"><CheckCircle size={11} /> Agotado</span>
                          ) : (
                            <span className="text-emerald-600 flex items-center gap-1 font-semibold"><CheckCircle size={11} /> Activo</span>
                          )}
                        </div>
                      </div>

                      {!isInactive && (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() => {
                            haptics.light();
                            navigate(`/?servicio_id=${bill.servicio}`);
                          }}
                          className="!bg-[#F9F6ED] !text-[#C5A059] hover:!bg-[#C5A059] hover:!text-white border border-[#C5A059]/40 text-xs font-bold rounded-full px-3.5"
                        >
                          Agendar turno
                        </Button>
                      )}
                    </div>

                    <div className="mb-5">
                      <div className="flex justify-between text-xs mb-1.5 font-medium">
                        <span className={isInactive ? 'text-neutral-400' : 'text-neutral-600'}>
                          <strong className={`text-base font-mono ${isInactive ? '' : 'text-[#C5A059]'}`}>{bill.sesiones_restantes}</strong> restantes
                        </span>
                        <span className="text-neutral-400 font-mono text-[11px] self-end">de {bill.sesiones_totales} totales</span>
                      </div>
                      <div className="w-full bg-neutral-100 rounded-full h-2 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${progress}%` }}
                          transition={{ duration: 0.8 }}
                          className={`h-full rounded-full ${isInactive ? 'bg-neutral-300' : 'bg-gradient-to-r from-[#C5A059] to-[#E5C788]'}`}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-between text-[11px] font-mono text-neutral-400 bg-neutral-50 p-3 rounded-xl border border-neutral-100">
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

      {/* MODAL REPROGRAMAR (FireSeed UI Modal) */}
      <Modal
        isOpen={Boolean(turnoToReschedule)}
        onClose={() => setTurnoToReschedule(null)}
        title="Reprogramar Turno"
        description={turnoToReschedule ? `Turno actual: ${turnoToReschedule.fecha} a las ${String(turnoToReschedule.hora_inicio || '').slice(0, 5)} hs` : ''}
        className="bg-white border border-neutral-200 text-[#34236F]"
      >
        <div className="space-y-5">
          <div className="p-3.5 rounded-xl bg-[#F9F6ED] border border-[#C5A059]/30 text-xs text-[#34236F]">
            <p className="font-bold text-sm font-serif">{turnoToReschedule?.servicio_detalle?.nombre}</p>
            <p className="text-[#C5A059] font-medium mt-0.5">Se actualizará en tiempo real con Google Calendar.</p>
          </div>

          <div>
            <DatePicker
              label="Nueva Fecha"
              placeholder="Seleccionar nueva fecha..."
              value={newFecha ? new Date(`${newFecha}T12:00:00`) : null}
              minDate={new Date()}
              className="estetica-datepicker"
              onChange={(d: Date) => {
                haptics.light();
                const y = d.getFullYear();
                const m = String(d.getMonth() + 1).padStart(2, '0');
                const day = String(d.getDate()).padStart(2, '0');
                setNewFecha(`${y}-${m}-${day}`);
                setNewHora('');
              }}
            />
          </div>

          {newFecha && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-[#34236F] mb-2">Nuevo Horario</label>
              {loadingHorarios ? (
                <p className="text-xs text-neutral-500 py-2">Consultando disponibilidad en Google Calendar...</p>
              ) : horariosDisponibles.length === 0 ? (
                <p className="text-xs text-amber-700 py-2">No hay horarios libres en esta fecha.</p>
              ) : (
                <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                  {horariosDisponibles.map(h => (
                    <button
                      key={h}
                      type="button"
                      onClick={() => {
                        haptics.light();
                        setNewHora(h);
                      }}
                      className={`px-3.5 py-2 text-xs font-bold rounded-xl border transition-all cursor-pointer ${
                        newHora === h
                          ? 'bg-[#C5A059] text-white border-[#C5A059]'
                          : 'border-neutral-200 text-[#34236F] hover:border-[#C5A059]'
                      }`}
                    >
                      {h} hs
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="flex gap-3 pt-3 border-t border-neutral-100">
            <Button
              variant="outline"
              size="md"
              onClick={() => setTurnoToReschedule(null)}
              className="flex-1 text-xs border-neutral-200 text-neutral-600 rounded-xl"
            >
              Volver
            </Button>
            <Button
              variant="glow"
              size="md"
              disabled={!newFecha || !newHora || rescheduling}
              onClick={handleConfirmReschedule}
              className="flex-1 text-xs !bg-[#C5A059] !text-white hover:!bg-[#B38E4C] font-bold rounded-xl"
            >
              {rescheduling ? 'Guardando...' : 'Confirmar Cambio'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* MODAL CANCELAR (FireSeed UI ConfirmModal) */}
      <ConfirmModal
        isOpen={Boolean(turnoToCancel)}
        onClose={() => setTurnoToCancel(null)}
        onConfirm={handleConfirmCancel}
        title="¿Cancelar este turno?"
        message={turnoToCancel ? `Estás por cancelar tu turno de ${turnoToCancel.servicio_detalle?.nombre} del día ${turnoToCancel.fecha} a las ${String(turnoToCancel.hora_inicio || '').slice(0, 5)} hs.\n\nLa sesión será reintegrada automáticamente a tu billetera y el evento se quitará de Google Calendar.` : ''}
        confirmText={canceling ? "Cancelando..." : "Sí, cancelar turno"}
        cancelText="No, mantener turno"
        isDestructive
      />
    </div>
  );
};