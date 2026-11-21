import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Stepper,
  Card,
  CardTitle,
  CardDescription,
  Badge,
  Button,
  FeedbackButton,
  Callout,
  EmptyState,
  AnimateIn,
  haptics
} from 'fireseed-ui';
import { Calendar, Clock, Sparkles, CheckCircle2, WalletCards, ArrowLeft, ShoppingBag, MapPin } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

const calcularHoraFinStr = (horaInicio: string, duracionMinutos: number): string => {
  if (!horaInicio) return '';
  const [hh, mm] = horaInicio.split(':').map(Number);
  if (isNaN(hh) || isNaN(mm)) return '';
  const totalMin = hh * 60 + mm + (duracionMinutos || 60);
  const endH = Math.floor(totalMin / 60) % 24;
  const endM = totalMin % 60;
  return `${String(endH).padStart(2, '0')}:${String(endM).padStart(2, '0')}`;
};

export const BookingFunnel = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [servicios, setServicios] = useState<any[]>([]);
  const [billeteras, setBilleteras] = useState<any[]>([]);
  const [selectedServicio, setSelectedServicio] = useState<any>(null);

  const [fecha, setFecha] = useState<string>('');
  const [horarios, setHorarios] = useState<string[]>([]);
  const [selectedHora, setSelectedHora] = useState<string>('');

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/servicios/'),
      api.get('/billeteras/').catch(() => ({ data: [] }))
    ])
      .then(([resServicios, resBilleteras]) => {
        const activos = (resServicios.data || []).filter((s: any) => s.is_active !== false);
        setServicios(activos);
        setBilleteras(resBilleteras.data || []);

        const preselectedId = searchParams.get('servicio_id');
        if (preselectedId) {
          const found = activos.find((s: any) => String(s.id) === String(preselectedId));
          if (found) {
            setSelectedServicio(found);
            setStep(2);
          }
        }
      })
      .catch(() => toast.error('Error cargando servicios'));
  }, [searchParams]);

  useEffect(() => {
    if (fecha && selectedServicio) {
      setLoading(true);
      api.get(`/disponibilidad/?fecha=${fecha}&servicio_id=${selectedServicio.id}`)
        .then(res => {
          setHorarios(res.data || []);
        })
        .catch(() => toast.error('Error cargando horarios'))
        .finally(() => setLoading(false));
    }
  }, [fecha, selectedServicio]);

  const getSesionesDisponibles = (servicioId: string): number => {
    return billeteras
      .filter(b => String(b.servicio) === String(servicioId) && b.estado === 'ACTIVO' && b.sesiones_restantes > 0)
      .reduce((acc, b) => acc + Number(b.sesiones_restantes || 0), 0);
  };

  const handleConfirm = async () => {
    if (!selectedServicio || !fecha || !selectedHora) return;
    try {
      setLoading(true);
      const horaFin = calcularHoraFinStr(selectedHora, selectedServicio.duracion_minutos);
      await api.post('/estetica-turnos/', {
        servicio: selectedServicio.id,
        fecha: fecha,
        hora_inicio: selectedHora,
        hora_fin: horaFin || undefined,
      });
      toast.success('¡Turno agendado con éxito!');
      api.get('/billeteras/').then(res => setBilleteras(res.data || [])).catch(() => {});
      setStep(4);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Ocurrió un error al agendar.');
    } finally {
      setLoading(false);
    }
  };

  const fadeVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 }
  };

  const sesionesServicioActual = selectedServicio ? getSesionesDisponibles(selectedServicio.id) : 0;
  const horaFinCalculada = selectedServicio && selectedHora
    ? calcularHoraFinStr(selectedHora, selectedServicio.duracion_minutos)
    : '';

  const buildGoogleCalendarUrl = () => {
    if (!selectedServicio || !fecha || !selectedHora) return '#';
    const horaFin = horaFinCalculada || selectedHora;
    const fCompact = fecha.replace(/-/g, '');
    const hStartCompact = selectedHora.replace(/:/g, '').padEnd(4, '0') + '00';
    const hEndCompact = horaFin.replace(/:/g, '').padEnd(4, '0') + '00';
    const text = encodeURIComponent(`Turno: ${selectedServicio.nombre} - Violett Estética`);
    const details = encodeURIComponent(
      `Turno confirmado para ${selectedServicio.nombre} (${selectedServicio.duracion_minutos} min).\nDirección: Comisionado Indart 2822, San Justo.\nAtención con turno previo.`
    );
    const location = encodeURIComponent('Comisionado Indart 2822, San Justo, Buenos Aires');
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${text}&dates=${fCompact}T${hStartCompact}/${fCompact}T${hEndCompact}&details=${details}&location=${location}&ctz=America/Argentina/Buenos_Aires`;
  };

  const stepperItems = [
    { title: 'Tratamiento', description: 'Elegí el servicio' },
    { title: 'Día y Hora', description: 'Agenda tu turno' },
    { title: 'Confirmación', description: 'Revisa y reserva' },
  ];

  return (
    <div className="w-full pb-20">
      {/* Interactive Stepper from Fireseed UI */}
      <div className="mb-8 pt-2">
        <Stepper
          steps={stepperItems}
          currentStep={step >= 4 ? 2 : step - 1}
          onStepClick={(stepIndex) => {
            if (stepIndex < step - 1 && step < 4) {
              haptics.selection();
              setStep(stepIndex + 1);
            }
          }}
          className="max-w-xl mx-auto"
        />
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div key="step1" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-[#FFF8EE] font-serif">Tratamientos Disponibles</h1>
                <p className="text-xs sm:text-sm text-[#FFF8EE]/60 mt-0.5">Seleccioná el procedimiento estético para tu sesión</p>
              </div>
              <Badge variant="glow" size="sm">Exclusivo Violett</Badge>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {servicios.map(srv => {
                const disponibles = getSesionesDisponibles(srv.id);
                return (
                  <Card
                    key={srv.id}
                    variant="elevated"
                    hoverable
                    onClick={() => {
                      haptics.light();
                      setSelectedServicio(srv);
                      setSelectedHora('');
                      setStep(2);
                    }}
                    className="cursor-pointer border border-[#C5A059]/25 bg-[#190826]/80 hover:border-[#C5A059] transition-all group p-6 flex flex-col justify-between rounded-2xl"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <CardTitle className="text-lg font-bold text-[#FFF8EE] group-hover:text-[#C5A059] transition-colors font-serif">
                          {srv.nombre}
                        </CardTitle>
                        {disponibles > 0 ? (
                          <Badge variant="success" size="sm" dot>
                            {disponibles} disp.
                          </Badge>
                        ) : (
                          <Badge variant="secondary" size="sm">
                            Sin sesiones
                          </Badge>
                        )}
                      </div>
                      {srv.descripcion && (
                        <CardDescription className="text-xs text-[#FFF8EE]/60 line-clamp-2 mb-4 leading-relaxed">
                          {srv.descripcion}
                        </CardDescription>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-white/10 mt-3">
                      <span className="text-xs text-[#FFF8EE]/60 flex items-center gap-1.5 font-medium">
                        <Clock size={13} className="text-[#C5A059]" /> {srv.duracion_minutos} min
                      </span>
                      <span className="font-bold text-[#C5A059] text-base font-mono">
                        ${Number(srv.precio_base).toLocaleString('es-AR')}
                      </span>
                    </div>
                  </Card>
                );
              })}
            </div>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="step2" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="space-y-6">
            <Card variant="elevated" className="p-6 sm:p-8 bg-[#190826]/90 border border-[#C5A059]/25 rounded-2xl space-y-6">
              <div className="flex items-center justify-between flex-wrap gap-2 pb-4 border-b border-white/10">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    haptics.light();
                    setStep(1);
                  }}
                  className="text-xs text-[#FFF8EE]/70 hover:text-[#FFF8EE] hover:bg-white/5"
                >
                  <ArrowLeft size={14} className="mr-1.5" /> Cambiar tratamiento
                </Button>
                <div className="text-right">
                  <p className="text-[10px] text-[#C5A059] uppercase tracking-wider font-bold">Tratamiento seleccionado</p>
                  <p className="text-sm font-bold text-[#FFF8EE] font-serif">{selectedServicio?.nombre} ({selectedServicio?.duracion_minutos} min)</p>
                </div>
              </div>

              {sesionesServicioActual === 0 && (
                <Callout
                  variant="warning"
                  title={`No tenés sesiones activas para ${selectedServicio?.nombre}`}
                  className="border-amber-500/30 bg-amber-500/10 text-amber-200"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-1.5">
                    <p className="text-xs text-[#FFF8EE]/80">Para confirmar la reserva necesitarás adquirir un paquete en la tienda.</p>
                    <Link to="/tienda">
                      <Button
                        variant="solid"
                        size="sm"
                        onClick={() => haptics.selection()}
                        className="!bg-[#C5A059] !text-[#150720] hover:!bg-[#B38E4C] text-xs font-bold shrink-0"
                      >
                        <ShoppingBag size={13} className="mr-1.5" /> Ir a la Tienda
                      </Button>
                    </Link>
                  </div>
                </Callout>
              )}

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#C5A059] mb-2 flex items-center gap-1.5">
                  <Calendar size={14} className="text-[#C5A059]" /> Seleccioná la fecha
                </label>
                <div className="relative">
                  <input
                    type="date"
                    value={fecha}
                    onChange={e => {
                      haptics.light();
                      setFecha(e.target.value);
                      setSelectedHora('');
                    }}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full p-4 rounded-xl bg-white/5 border border-white/15 text-[#FFF8EE] focus:border-[#C5A059] focus:ring-1 focus:ring-[#C5A059] outline-none transition-all font-medium text-sm"
                  />
                </div>
              </div>

              {fecha && (
                <div className="pt-2">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#C5A059] mb-3 flex items-center gap-1.5">
                    <Clock size={14} className="text-[#C5A059]" /> Horarios disponibles (Sincronizado con Google Calendar)
                  </label>
                  {loading ? (
                    <div className="p-8 text-center text-xs text-[#FFF8EE]/60 flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-[#C5A059] border-t-transparent rounded-full animate-spin"></div>
                      Buscando disponibilidad en tiempo real...
                    </div>
                  ) : horarios.length === 0 ? (
                    <EmptyState
                      title="Sin horarios disponibles"
                      description="No hay turnos libres para esta fecha. Probá seleccionando otro día en el selector."
                      icon={<Clock className="w-6 h-6 text-[#C5A059]" />}
                      className="my-2 border-[#C5A059]/20 bg-white/5"
                    />
                  ) : (
                    <div className="flex flex-wrap gap-2.5">
                      {horarios.map(hora => (
                        <Button
                          key={hora}
                          variant={selectedHora === hora ? "glow" : "outline"}
                          size="md"
                          onClick={() => {
                            haptics.selection();
                            setSelectedHora(hora);
                            setStep(3);
                          }}
                          className={`rounded-full px-5 py-2 text-xs font-semibold transition-all ${
                            selectedHora === hora
                              ? '!bg-[#C5A059] !text-[#150720] !border-[#C5A059] shadow-md shadow-[#C5A059]/25 font-bold'
                              : 'border-[#C5A059]/30 text-[#FFF8EE] hover:border-[#C5A059] hover:bg-[#C5A059]/10'
                          }`}
                        >
                          {hora} hs
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </Card>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="step3" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="space-y-6">
            <Card variant="glow" className="p-6 sm:p-8 bg-[#190826]/95 border-[#C5A059]/35 rounded-2xl space-y-6">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  haptics.light();
                  setStep(2);
                }}
                className="text-xs text-[#FFF8EE]/70 hover:text-[#FFF8EE] hover:bg-white/5"
              >
                <ArrowLeft size={14} className="mr-1.5" /> Cambiar fecha u horario
              </Button>

              <div className="bg-white/5 p-6 rounded-2xl border border-white/10 space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles size={18} className="text-[#C5A059]" />
                  <h3 className="font-bold text-lg text-[#FFF8EE] font-serif">Resumen de tu turno</h3>
                </div>

                <div className="space-y-3 text-xs sm:text-sm text-[#FFF8EE]/80">
                  <div className="flex justify-between py-2 border-b border-white/10">
                    <span className="text-[#FFF8EE]/50">Tratamiento</span>
                    <strong className="text-[#FFF8EE] font-serif">{selectedServicio?.nombre}</strong>
                  </div>
                  <div className="flex justify-between py-2 border-b border-white/10">
                    <span className="text-[#FFF8EE]/50">Fecha</span>
                    <strong className="text-[#FFF8EE] font-mono">{fecha}</strong>
                  </div>
                  <div className="flex justify-between py-2 border-b border-white/10">
                    <span className="text-[#FFF8EE]/50">Horario</span>
                    <strong className="text-[#C5A059] font-mono">
                      {selectedHora} a {horaFinCalculada} hs ({selectedServicio?.duracion_minutos} min)
                    </strong>
                  </div>
                  <div className="flex justify-between py-2 border-b border-white/10">
                    <span className="text-[#FFF8EE]/50 flex items-center gap-1">
                      <MapPin size={13} className="text-[#C5A059]" /> Ubicación
                    </span>
                    <span className="text-[#FFF8EE] text-right">Comisionado Indart 2822, San Justo</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-[#FFF8EE]/50">Tu saldo actual</span>
                    <strong className={sesionesServicioActual > 0 ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
                      {sesionesServicioActual} {sesionesServicioActual === 1 ? 'sesión disponible' : 'sesiones disponibles'}
                    </strong>
                  </div>
                </div>
              </div>

              {sesionesServicioActual > 0 ? (
                <FeedbackButton
                  initialText="CONFIRMAR Y AGENDAR (Usa 1 sesión)"
                  loadingText="Sincronizando con Google Calendar..."
                  successText="¡Turno Agendado con Éxito!"
                  variant="solid"
                  size="lg"
                  disabled={loading}
                  onClick={handleConfirm}
                  className="w-full !bg-gradient-to-r !from-[#C5A059] !to-[#E5C788] !text-[#150720] font-bold text-sm shadow-lg shadow-[#C5A059]/25 cursor-pointer py-4"
                />
              ) : (
                <div className="space-y-3">
                  <Callout variant="warning" title="Saldo insuficiente">
                    No contás con sesiones activas en tu billetera para este tratamiento. Adquirí tu paquete en la tienda para poder confirmar.
                  </Callout>
                  <Link to="/tienda">
                    <Button
                      variant="solid"
                      size="lg"
                      onClick={() => haptics.selection()}
                      className="w-full !bg-[#C5A059] !text-[#150720] hover:!bg-[#B38E4C] font-bold text-sm flex items-center justify-center gap-2 py-4"
                    >
                      <ShoppingBag size={16} /> Adquirir Paquete en la Tienda
                    </Button>
                  </Link>
                </div>
              )}
            </Card>
          </motion.div>
        )}

        {step === 4 && (
          <motion.div key="step4" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="text-center">
            <Card variant="elevated" className="p-8 sm:p-12 bg-[#190826]/95 border-[#C5A059]/30 rounded-3xl max-w-lg mx-auto space-y-6">
              <AnimateIn>
                <div className="w-20 h-20 bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 rounded-full flex items-center justify-center mx-auto shadow-inner">
                  <CheckCircle2 size={42} />
                </div>
              </AnimateIn>

              <div>
                <h2 className="text-2xl sm:text-3xl font-bold text-[#FFF8EE] font-serif mb-2">¡Turno Confirmado!</h2>
                <p className="text-xs sm:text-sm text-[#FFF8EE]/70 leading-relaxed">
                  Te esperamos el <strong className="text-[#FFF8EE]">{fecha}</strong> a las <strong className="text-[#C5A059]">{selectedHora} hs</strong> para tu sesión de <strong className="text-[#FFF8EE] font-serif">{selectedServicio?.nombre}</strong>.
                </p>
              </div>

              <div className="pt-2">
                <a
                  href={buildGoogleCalendarUrl()}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => haptics.selection()}
                  className="block"
                >
                  <Button
                    variant="glow"
                    size="lg"
                    className="w-full !bg-[#C5A059] !text-[#150720] hover:!bg-[#B38E4C] font-bold text-xs sm:text-sm shadow-md shadow-[#C5A059]/20"
                  >
                    <Calendar size={16} className="mr-2" /> Añadir a mi Google Calendar
                  </Button>
                </a>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <Button
                  variant="outline"
                  size="md"
                  onClick={() => {
                    haptics.light();
                    navigate('/mi-cuenta');
                  }}
                  className="flex-1 border-white/20 text-[#FFF8EE] hover:bg-white/10 text-xs"
                >
                  Ver mis turnos en Mi Cuenta
                </Button>
                <Button
                  variant="ghost"
                  size="md"
                  onClick={() => {
                    haptics.light();
                    setStep(1);
                    setFecha('');
                    setSelectedHora('');
                  }}
                  className="flex-1 text-[#FFF8EE]/70 hover:text-[#FFF8EE] hover:bg-white/5 text-xs"
                >
                  Agendar otro turno
                </Button>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
