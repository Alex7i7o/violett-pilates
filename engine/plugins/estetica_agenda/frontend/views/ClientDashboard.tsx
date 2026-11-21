import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Card,
  CardTitle,
  Badge,
  Button,
  Modal,
  ConfirmModal,
  EmptyState,
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
          <div key={i} className="h-32 bg-white/5 border border-white/10 rounded-2xl animate-pulse"></div>
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
            <div className="p-2.5 bg-[#C5A059]/15 border border-[#C5A059]/30 text-[#C5A059] rounded-xl shadow-sm">
              <Calendar size={22} />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-[#FFF8EE] font-serif tracking-tight">Mis Turnos</h2>
              <p className="text-xs text-[#FFF8EE]/60">Gestioná tus próximas visitas o reprogramá si lo necesitás</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {historialTurnos.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  haptics.selection();
                  setShowHistory(!showHistory);
                }}
                className="text-xs border-white/15 text-[#FFF8EE]/80 hover:bg-white/5"
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
                className="text-xs !bg-[#C5A059] !text-[#150720] hover:!bg-[#B38E4C] font-bold"
              >
                <Plus size={14} className="mr-1" /> Nuevo Turno
              </Button>
            </Link>
          </div>
        </div>

        {!showHistory ? (
          proximosTurnos.length === 0 ? (
            <EmptyState
              title="No tenés próximos turnos agendados"
              description="Elegí un tratamiento y reservá tu horario en segundos."
              icon={<Calendar size={28} className="text-[#C5A059]" />}
              action={
                <Link to="/">
                  <Button variant="glow" size="md" className="!bg-[#C5A059] !text-[#150720] font-bold text-xs">
                    <Sparkles size={14} className="mr-1.5" /> Reservar un turno ahora
                  </Button>
                </Link>
              }
              className="border-[#C5A059]/25 bg-[#190826]/70 rounded-2xl p-8"
            />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {proximosTurnos.map(turno => (
                <Card
                  key={turno.id}
                  variant="elevated"
                  className="bg-[#190826]/90 border border-[#C5A059]/25 p-6 rounded-2xl flex flex-col justify-between gap-4"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <Badge variant="success" size="sm" dot>
                        Confirmado
                      </Badge>
                      <span className="text-xs font-mono text-[#FFF8EE]/60">
                        {turno.servicio_detalle?.duracion_minutos || 60} min
                      </span>
                    </div>
                    <CardTitle className="text-lg font-bold text-[#FFF8EE] font-serif mb-2">
                      {turno.servicio_detalle?.nombre || 'Tratamiento Estético'}
                    </CardTitle>
                    <div className="space-y-1.5 text-xs text-[#FFF8EE]/70">
                      <p className="flex items-center gap-2 font-medium text-[#FFF8EE]">
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

                  <div className="flex items-center gap-2 pt-3 border-t border-white/10">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        haptics.light();
                        setTurnoToReschedule(turno);
                        setNewFecha(turno.fecha);
                        setNewHora('');
                      }}
                      className="flex-1 text-xs border-[#C5A059]/30 text-[#FFF8EE] hover:bg-[#C5A059]/10"
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
                      className="text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
                    >
                      <XCircle size={13} className="mr-1" /> Cancelar
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {historialTurnos.map(turno => {
              const badgeVariant =
                turno.estado === 'ASISTIO'
                  ? 'success'
                  : turno.estado === 'CANCELADA'
                  ? 'secondary'
                  : 'warning';
              return (
                <Card
                  key={turno.id}
                  variant="default"
                  className="bg-[#190826]/60 border border-white/10 p-5 rounded-2xl flex items-center justify-between gap-4"
                >
                  <div>
                    <h4 className="font-bold text-sm text-[#FFF8EE] font-serif">
                      {turno.servicio_detalle?.nombre || 'Tratamiento'}
                    </h4>
                    <p className="text-xs text-[#FFF8EE]/50 mt-0.5 font-mono">
                      {turno.fecha} • {String(turno.hora_inicio || '').slice(0, 5)} hs
                    </p>
                  </div>
                  <Badge variant={badgeVariant as any} size="sm">
                    {turno.estado === 'ASISTIO'
                      ? 'Asistió'
                      : turno.estado === 'NO_ASISTIO'
                      ? 'Ausente'
                      : turno.estado === 'CANCELADA'
                      ? 'Cancelado'
                      : turno.estado}
                  </Badge>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {/* SECCIÓN 2: MI BILLETERA */}
      <section>
        <div className="flex items-center justify-between gap-3 mb-6 px-1">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-[#C5A059]/15 border border-[#C5A059]/30 text-[#C5A059] rounded-xl shadow-sm">
              <WalletCards size={22} />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-[#FFF8EE] font-serif tracking-tight">Mi Billetera</h2>
              <p className="text-xs text-[#FFF8EE]/60">Tus paquetes de sesiones adquiridos y su saldo disponible</p>
            </div>
          </div>
        </div>

        {billeteras.length === 0 ? (
          <EmptyState
            title="No tenés paquetes activos en tu billetera"
            description="Adquirí sesiones con descuento en la tienda y usalas cuando quieras."
            icon={<WalletCards size={28} className="text-[#C5A059]" />}
            action={
              <Link to="/tienda">
                <Button variant="glow" size="md" className="!bg-[#C5A059] !text-[#150720] font-bold text-xs">
                  Ir a la Tienda de Paquetes
                </Button>
              </Link>
            }
            className="border-[#C5A059]/25 bg-[#190826]/70 rounded-2xl p-8"
          />
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
                      ? 'bg-white/5 text-[#FFF8EE]/40 border-white/10'
                      : 'bg-[#190826]/90 shadow-md border-[#C5A059]/25 text-[#FFF8EE]'
                  }`}
                >
                  <div>
                    <div className="flex justify-between items-start mb-5">
                      <div>
                        <h3 className={`font-bold text-lg leading-tight mb-1 font-serif ${isInactive ? 'text-[#FFF8EE]/50' : 'text-[#FFF8EE]'}`}>
                          {bill.servicio_detalle?.nombre || 'Servicio'}
                        </h3>
                        <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider">
                          {isVencido ? (
                            <Badge variant="error" size="sm"><Clock size={11} className="mr-1" /> Vencido</Badge>
                          ) : isAgotado ? (
                            <Badge variant="warning" size="sm"><CheckCircle size={11} className="mr-1" /> Agotado</Badge>
                          ) : (
                            <Badge variant="success" size="sm" dot><CheckCircle size={11} className="mr-1" /> Activo</Badge>
                          )}
                        </div>
                      </div>

                      {!isInactive && (
                        <Button
                          variant="glow"
                          size="sm"
                          onClick={() => {
                            haptics.selection();
                            navigate(`/?servicio_id=${bill.servicio}`);
                          }}
                          className="!bg-[#C5A059] !text-[#150720] hover:!bg-[#B38E4C] text-xs font-bold"
                        >
                          Agendar turno
                        </Button>
                      )}
                    </div>

                    <div className="mb-5">
                      <div className="flex justify-between text-xs mb-1.5 font-medium">
                        <span className={isInactive ? 'text-[#FFF8EE]/40' : 'text-[#FFF8EE]/70'}>
                          <strong className={`text-base font-mono ${isInactive ? '' : 'text-[#C5A059]'}`}>{bill.sesiones_restantes}</strong> restantes
                        </span>
                        <span className="text-[#FFF8EE]/50 font-mono text-[11px] self-end">de {bill.sesiones_totales} totales</span>
                      </div>
                      <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${progress}%` }}
                          transition={{ duration: 0.8 }}
                          className={`h-full rounded-full ${isInactive ? 'bg-white/20' : 'bg-gradient-to-r from-[#C5A059] to-[#E5C788]'}`}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-between text-[11px] font-mono text-[#FFF8EE]/50 bg-white/5 p-3 rounded-xl border border-white/5">
                    <div>
                      <p className="uppercase tracking-wider text-[9px] mb-0.5 opacity-60">Compra</p>
                      <p>{bill.fecha_compra}</p>
                    </div>
                    <div className="text-right">
                      <p className="uppercase tracking-wider text-[9px] mb-0.5 opacity-60">Vence</p>
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
        className="bg-[#190826] border border-[#C5A059]/30 text-[#FFF8EE]"
      >
        <div className="space-y-5">
          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs text-[#FFF8EE]/80">
            <p className="font-bold text-[#FFF8EE] text-sm font-serif">{turnoToReschedule?.servicio_detalle?.nombre}</p>
            <p className="text-[#C5A059] mt-0.5">Se actualizará en tiempo real con Google Calendar.</p>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#C5A059] mb-1.5">Nueva Fecha</label>
            <input
              type="date"
              min={todayStr}
              value={newFecha}
              onChange={e => {
                haptics.light();
                setNewFecha(e.target.value);
                setNewHora('');
              }}
              className="w-full p-3 rounded-xl bg-white/5 border border-white/15 text-[#FFF8EE] text-sm focus:border-[#C5A059] outline-none"
            />
          </div>

          {newFecha && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-[#C5A059] mb-2">Nuevo Horario</label>
              {loadingHorarios ? (
                <p className="text-xs text-[#FFF8EE]/60 py-2">Consultando disponibilidad en Google Calendar...</p>
              ) : horariosDisponibles.length === 0 ? (
                <p className="text-xs text-amber-300 py-2">No hay horarios libres en esta fecha.</p>
              ) : (
                <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                  {horariosDisponibles.map(h => (
                    <Button
                      key={h}
                      variant={newHora === h ? "glow" : "outline"}
                      size="sm"
                      onClick={() => {
                        haptics.selection();
                        setNewHora(h);
                      }}
                      className={`text-xs rounded-xl ${
                        newHora === h
                          ? '!bg-[#C5A059] !text-[#150720] !border-[#C5A059]'
                          : 'border-white/20 text-[#FFF8EE]'
                      }`}
                    >
                      {h} hs
                    </Button>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="flex gap-3 pt-3 border-t border-white/10">
            <Button
              variant="outline"
              size="md"
              onClick={() => setTurnoToReschedule(null)}
              className="flex-1 text-xs border-white/20 text-[#FFF8EE]"
            >
              Volver
            </Button>
            <Button
              variant="glow"
              size="md"
              disabled={!newFecha || !newHora || rescheduling}
              onClick={handleConfirmReschedule}
              className="flex-1 text-xs !bg-[#C5A059] !text-[#150720] font-bold"
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