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
  DatePicker,
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
      {/* Stepper interactivo */}
      <div className="mb-8 pt-2">
        <Stepper
          steps={stepperItems}
          currentStep={step >= 4 ? 2 : step - 1}
          onStepClick={(stepIndex) => {
            if (stepIndex < step - 1 && step < 4) {
              haptics.light();
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
                <h1 className="text-2xl sm:text-3xl font-bold text-[#34236F] font-serif">Tratamientos Disponibles</h1>
                <p className="text-xs sm:text-sm text-neutral-500 mt-0.5">Seleccioná el procedimiento estético para tu sesión</p>
              </div>
              <Badge variant="solid" size="sm" className="!bg-[#F9F6ED] !text-[#C5A059] !border-[#C5A059]/40 font-bold">
                Exclusivo Violett
              </Badge>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {servicios.map(srv => {
                const disponibles = getSesionesDisponibles(srv.id);
                return (
                  <button
                    key={srv.id}
                    onClick={() => {
                      haptics.light();
                      setSelectedServicio(srv);
                      setSelectedHora('');
                      setStep(2);
                    }}
                    className="text-left p-6 rounded-2xl bg-white border-2 border-neutral-100 hover:border-[#C5A059] shadow-soft hover:shadow-md transition-all flex flex-col justify-between group cursor-pointer"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h3 className="text-lg font-bold text-[#34236F] group-hover:text-[#C5A059] transition-colors font-serif">
                          {srv.nombre}
                        </h3>
                        {disponibles > 0 ? (
                          <span className="shrink-0 text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                            <WalletCards size={12} /> {disponibles} disp.
                          </span>
                        ) : (
                          <span className="shrink-0 text-[11px] font-medium px-2.5 py-1 rounded-full bg-neutral-100 text-neutral-500">
                            Sin sesiones
                          </span>
                        )}
                      </div>
                      {srv.descripcion && (
                        <p className="text-xs text-neutral-500 line-clamp-2 mb-4 leading-relaxed">
                          {srv.descripcion}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-neutral-100 mt-3">
                      <span className="text-xs text-neutral-500 flex items-center gap-1.5 font-medium">
                        <Clock size={14} className="text-[#C5A059]" /> {srv.duracion_minutos} min
                      </span>
                      <span className="font-bold text-[#C5A059] text-base font-mono">
                        ${Number(srv.precio_base).toLocaleString('es-AR')}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="step2" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="space-y-6">
            <div className="bg-white p-6 sm:p-8 rounded-2xl border border-neutral-100 shadow-soft space-y-6">
              <div className="flex items-center justify-between flex-wrap gap-2 pb-4 border-b border-neutral-100">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    haptics.light();
                    setStep(1);
                  }}
                  className="text-xs text-neutral-600 hover:text-[#34236F] hover:bg-neutral-50"
                >
                  <ArrowLeft size={14} className="mr-1.5" /> Cambiar tratamiento
                </Button>
                <div className="text-right">
                  <p className="text-[10px] text-[#C5A059] uppercase tracking-wider font-bold">Tratamiento seleccionado</p>
                  <p className="text-sm font-bold text-[#34236F] font-serif">{selectedServicio?.nombre} ({selectedServicio?.duracion_minutos} min)</p>
                </div>
              </div>

              {sesionesServicioActual === 0 && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <p className="font-bold text-sm mb-0.5">No tenés sesiones activas para {selectedServicio?.nombre}</p>
                    <p className="text-neutral-600">Para confirmar la reserva necesitarás adquirir un paquete en la tienda.</p>
                  </div>
                  <Link to="/tienda">
                    <Button
                      variant="solid"
                      size="sm"
                      onClick={() => haptics.light()}
                      className="!bg-[#C5A059] !text-white hover:!bg-[#B38E4C] text-xs font-bold shrink-0"
                    >
                      <ShoppingBag size={13} className="mr-1.5" /> Ir a la Tienda
                    </Button>
                  </Link>
                </div>
              )}

              <div className="space-y-1">
                <DatePicker
                  label="Seleccioná la fecha"
                  placeholder="Elegí el día para tu turno..."
                  value={fecha ? new Date(`${fecha}T12:00:00`) : null}
                  minDate={new Date()}
                  className="estetica-datepicker"
                  onChange={(d: Date) => {
                    haptics.light();
                    const y = d.getFullYear();
                    const m = String(d.getMonth() + 1).padStart(2, '0');
                    const day = String(d.getDate()).padStart(2, '0');
                    setFecha(`${y}-${m}-${day}`);
                    setSelectedHora('');
                  }}
                />
              </div>

              {fecha && (
                <div className="pt-2">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#34236F] mb-3 flex items-center gap-1.5">
                    <Clock size={14} className="text-[#C5A059]" /> Horarios disponibles (Sincronizado con Google Calendar)
                  </label>
                  {loading ? (
                    <div className="p-8 text-center text-xs text-neutral-500 flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-[#C5A059] border-t-transparent rounded-full animate-spin"></div>
                      Buscando disponibilidad en tiempo real...
                    </div>
                  ) : horarios.length === 0 ? (
                    <div className="p-8 text-center rounded-2xl bg-neutral-50 border border-neutral-100 text-xs text-neutral-500">
                      No hay turnos libres para esta fecha. Probá seleccionando otro día en el selector.
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2.5">
                      {horarios.map(hora => (
                        <button
                          key={hora}
                          onClick={() => {
                            haptics.light();
                            setSelectedHora(hora);
                            setStep(3);
                          }}
                          className={`px-5 py-2.5 rounded-full font-bold text-xs border-2 transition-all cursor-pointer ${
                            selectedHora === hora
                              ? 'bg-[#C5A059] text-white border-[#C5A059] shadow-md shadow-[#C5A059]/25'
                              : 'border-[#C5A059]/30 text-[#C5A059] hover:bg-[#C5A059] hover:text-white bg-white'
                          }`}
                        >
                          {hora} hs
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="step3" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="space-y-6">
            <div className="bg-white p-6 sm:p-8 rounded-2xl border border-neutral-100 shadow-soft space-y-6">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  haptics.light();
                  setStep(2);
                }}
                className="text-xs text-neutral-600 hover:text-[#34236F] hover:bg-neutral-50"
              >
                <ArrowLeft size={14} className="mr-1.5" /> Cambiar fecha u horario
              </Button>

              <div className="bg-[#F9F6ED] p-6 rounded-2xl border border-[#C5A059]/30 space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles size={18} className="text-[#C5A059]" />
                  <h3 className="font-bold text-lg text-[#34236F] font-serif">Resumen de tu turno</h3>
                </div>

                <div className="space-y-3 text-xs sm:text-sm text-[#34236F]/90">
                  <div className="flex justify-between py-2 border-b border-neutral-200/60">
                    <span className="text-neutral-500">Tratamiento</span>
                    <strong className="text-[#34236F] font-serif">{selectedServicio?.nombre}</strong>
                  </div>
                  <div className="flex justify-between py-2 border-b border-neutral-200/60">
                    <span className="text-neutral-500">Fecha</span>
                    <strong className="text-[#34236F] font-mono">{fecha}</strong>
                  </div>
                  <div className="flex justify-between py-2 border-b border-neutral-200/60">
                    <span className="text-neutral-500">Horario</span>
                    <strong className="text-[#C5A059] font-mono">
                      {selectedHora} a {horaFinCalculada} hs ({selectedServicio?.duracion_minutos} min)
                    </strong>
                  </div>
                  <div className="flex justify-between py-2 border-b border-neutral-200/60">
                    <span className="text-neutral-500 flex items-center gap-1">
                      <MapPin size={13} className="text-[#C5A059]" /> Ubicación
                    </span>
                    <span className="text-[#34236F] text-right">Comisionado Indart 2822, San Justo</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-neutral-500">Tu saldo actual</span>
                    <strong className={sesionesServicioActual > 0 ? 'text-emerald-600 font-semibold' : 'text-amber-600 font-semibold'}>
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
                  className="w-full !bg-[#C5A059] hover:!bg-[#B38E4C] !text-white font-bold text-sm shadow-md shadow-[#C5A059]/25 cursor-pointer py-4 rounded-xl"
                />
              ) : (
                <div className="space-y-3">
                  <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs">
                    No contás con sesiones activas en tu billetera para este tratamiento. Adquirí tu paquete en la tienda para poder confirmar.
                  </div>
                  <Link to="/tienda">
                    <Button
                      variant="solid"
                      size="lg"
                      onClick={() => haptics.light()}
                      className="w-full !bg-[#C5A059] !text-white hover:!bg-[#B38E4C] font-bold text-sm flex items-center justify-center gap-2 py-4 rounded-xl"
                    >
                      <ShoppingBag size={16} /> Adquirir Paquete en la Tienda
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {step === 4 && (
          <motion.div key="step4" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="text-center">
            <div className="bg-white p-8 sm:p-12 border border-neutral-100 shadow-soft rounded-3xl max-w-lg mx-auto space-y-6">
              <div className="w-20 h-20 bg-emerald-50 border border-emerald-200 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-sm">
                <CheckCircle2 size={42} />
              </div>

              <div>
                <h2 className="text-2xl sm:text-3xl font-bold text-[#34236F] font-serif mb-2">¡Turno Confirmado!</h2>
                <p className="text-xs sm:text-sm text-neutral-600 leading-relaxed">
                  Te esperamos el <strong className="text-[#34236F]">{fecha}</strong> a las <strong className="text-[#C5A059]">{selectedHora} hs</strong> para tu sesión de <strong className="text-[#34236F] font-serif">{selectedServicio?.nombre}</strong>.
                </p>
              </div>

              <div className="pt-2">
                <a
                  href={buildGoogleCalendarUrl()}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => haptics.light()}
                  className="block"
                >
                  <Button
                    variant="glow"
                    size="lg"
                    className="w-full !bg-[#C5A059] !text-white hover:!bg-[#B38E4C] font-bold text-xs sm:text-sm shadow-md shadow-[#C5A059]/20 rounded-xl"
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
                  className="flex-1 border-neutral-200 text-[#34236F] hover:bg-neutral-50 text-xs rounded-xl"
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
                  className="flex-1 text-neutral-500 hover:text-[#34236F] hover:bg-neutral-50 text-xs rounded-xl"
                >
                  Agendar otro turno
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};