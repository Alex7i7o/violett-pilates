import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Clock, Sparkles, CheckCircle2, WalletCards, ArrowLeft, ShoppingBag } from 'lucide-react';
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
      // Refresh wallets count
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

  return (
    <div className="w-full pb-20">
      <div className="mb-8">
        <span className="text-xs font-bold uppercase tracking-widest text-primary-main">
          Paso {step} de 3
        </span>
        <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 mt-1">
          {step === 1
            ? 'Elegí un tratamiento'
            : step === 2
            ? 'Elegí el día y horario'
            : step === 3
            ? 'Confirmá tu turno'
            : '¡Turno Confirmado!'}
        </h1>
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div key="step1" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="grid gap-4 sm:grid-cols-2">
            {servicios.map(srv => {
              const disponibles = getSesionesDisponibles(srv.id);
              return (
                <button
                  key={srv.id}
                  onClick={() => {
                    setSelectedServicio(srv);
                    setSelectedHora('');
                    setStep(2);
                  }}
                  className="text-left p-6 rounded-[1.75rem] bg-white border-2 border-neutral-100 hover:border-primary-main hover:shadow-md transition-all flex flex-col justify-between group"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className="font-bold text-lg text-neutral-900 group-hover:text-primary-main transition-colors">
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
                      <p className="text-xs text-neutral-500 line-clamp-2 mb-3">{srv.descripcion}</p>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-neutral-100 mt-2">
                    <span className="text-xs font-medium text-neutral-500 flex items-center gap-1">
                      <Clock size={14} className="text-primary-main" /> {srv.duracion_minutos} min
                    </span>
                    <span className="font-bold text-primary-main text-base">
                      ${Number(srv.precio_base).toLocaleString('es-AR')}
                    </span>
                  </div>
                </button>
              );
            })}
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="step2" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="space-y-6 bg-white p-6 sm:p-8 rounded-[2rem] border border-neutral-100 shadow-xs">
            <div className="flex items-center justify-between flex-wrap gap-2 pb-4 border-b border-neutral-100">
              <button
                onClick={() => setStep(1)}
                className="text-sm font-medium text-neutral-500 hover:text-neutral-900 flex items-center gap-1.5 transition-colors"
              >
                <ArrowLeft size={16} /> Cambiar tratamiento
              </button>
              <div className="text-right">
                <p className="text-xs text-neutral-400 uppercase font-bold">Tratamiento seleccionado</p>
                <p className="text-sm font-bold text-primary-main">{selectedServicio?.nombre} ({selectedServicio?.duracion_minutos} min)</p>
              </div>
            </div>

            {sesionesServicioActual === 0 && (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="text-xs text-amber-900">
                  <p className="font-bold text-sm mb-0.5">No tenés sesiones activas para {selectedServicio?.nombre}</p>
                  <p>Para confirmar la reserva necesitarás adquirir un paquete en la tienda.</p>
                </div>
                <Link
                  to="/tienda-paquetes"
                  className="shrink-0 px-4 py-2 rounded-xl bg-amber-600 text-white text-xs font-bold hover:bg-amber-700 transition-colors flex items-center gap-1.5 self-start sm:self-center"
                >
                  <ShoppingBag size={14} /> Ir a Paquetes
                </Link>
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-neutral-700 mb-2 flex items-center gap-1.5">
                <Calendar size={16} className="text-primary-main" /> Seleccioná la fecha
              </label>
              <input
                type="date"
                value={fecha}
                onChange={e => {
                  setFecha(e.target.value);
                  setSelectedHora('');
                }}
                min={new Date().toISOString().split('T')[0]}
                className="w-full p-4 rounded-xl border border-neutral-200 focus:border-primary-main focus:ring-1 focus:ring-primary-main outline-none transition-all font-medium"
              />
            </div>

            {fecha && (
              <div>
                <label className="block text-sm font-semibold text-neutral-700 mb-3 flex items-center gap-1.5">
                  <Clock size={16} className="text-primary-main" /> Horarios disponibles
                </label>
                {loading ? (
                  <p className="text-sm text-neutral-500 py-4">Buscando horarios disponibles...</p>
                ) : horarios.length === 0 ? (
                  <div className="p-6 rounded-2xl bg-neutral-50 text-center text-sm text-neutral-500 border border-neutral-100">
                    No hay horarios disponibles para esta fecha. Probá seleccionando otro día.
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-3">
                    {horarios.map(hora => (
                      <button
                        key={hora}
                        onClick={() => {
                          setSelectedHora(hora);
                          setStep(3);
                        }}
                        className="px-6 py-3 rounded-full font-semibold text-sm border-2 border-primary-main/30 text-primary-main hover:bg-primary-main hover:border-primary-main hover:text-white transition-all active:scale-95"
                      >
                        {hora} hs
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="step3" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="bg-white p-6 sm:p-8 rounded-[2rem] border border-neutral-100 shadow-xs">
            <button
              onClick={() => setStep(2)}
              className="text-sm font-medium text-neutral-500 hover:text-neutral-900 flex items-center gap-1.5 mb-6 transition-colors"
            >
              <ArrowLeft size={16} /> Cambiar fecha u horario
            </button>

            <div className="bg-neutral-50 p-6 rounded-2xl border border-neutral-100 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles size={18} className="text-primary-main" />
                <h3 className="font-bold text-lg text-neutral-900">Resumen de tu turno</h3>
              </div>
              <div className="space-y-3 text-sm text-neutral-600">
                <div className="flex justify-between py-2 border-b border-neutral-200/60">
                  <span className="text-neutral-500">Tratamiento</span>
                  <strong className="text-neutral-900">{selectedServicio?.nombre}</strong>
                </div>
                <div className="flex justify-between py-2 border-b border-neutral-200/60">
                  <span className="text-neutral-500">Fecha</span>
                  <strong className="text-neutral-900">{fecha}</strong>
                </div>
                <div className="flex justify-between py-2 border-b border-neutral-200/60">
                  <span className="text-neutral-500">Horario</span>
                  <strong className="text-neutral-900">
                    {selectedHora} a {horaFinCalculada} hs ({selectedServicio?.duracion_minutos} min)
                  </strong>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-neutral-500">Tu saldo actual</span>
                  <strong className={sesionesServicioActual > 0 ? 'text-emerald-600' : 'text-amber-600'}>
                    {sesionesServicioActual} {sesionesServicioActual === 1 ? 'sesión disponible' : 'sesiones disponibles'}
                  </strong>
                </div>
              </div>
            </div>

            {sesionesServicioActual > 0 ? (
              <button
                onClick={handleConfirm}
                disabled={loading}
                className="w-full py-4 rounded-2xl bg-primary-main text-white font-bold text-base hover:bg-primary-hover transition-colors disabled:opacity-50 shadow-md"
              >
                {loading ? 'Agendando...' : 'CONFIRMAR Y AGENDAR (Usa 1 sesión)'}
              </button>
            ) : (
              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm">
                  No contás con sesiones activas en tu billetera para este tratamiento. Adquirí tu paquete primero para poder reservar.
                </div>
                <Link
                  to="/tienda-paquetes"
                  className="w-full py-4 rounded-2xl bg-primary-main text-white font-bold text-base hover:bg-primary-hover transition-colors flex items-center justify-center gap-2"
                >
                  <ShoppingBag size={18} /> Adquirir Paquete en la Tienda
                </Link>
              </div>
            )}
          </motion.div>
        )}

        {step === 4 && (
          <motion.div key="step4" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="bg-white p-8 sm:p-12 rounded-[2rem] border border-neutral-100 text-center">
            <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 size={42} />
            </div>
            <h2 className="text-2xl font-bold text-neutral-900 mb-2">¡Turno Confirmado!</h2>
            <p className="text-neutral-500 mb-6">
              Te esperamos el <strong>{fecha}</strong> a las <strong>{selectedHora} hs</strong> para tu sesión de <strong>{selectedServicio?.nombre}</strong>.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
              <a
                href={buildGoogleCalendarUrl()}
                target="_blank"
                rel="noreferrer"
                className="px-6 py-3.5 rounded-xl bg-blue-50 text-blue-700 border border-blue-200 font-bold text-sm hover:bg-blue-100 transition-colors inline-flex items-center justify-center gap-2"
              >
                <Calendar size={17} /> Añadir a mi Google Calendar
              </a>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => navigate('/mi-cuenta')}
                className="px-6 py-3.5 rounded-xl bg-primary-main text-white font-bold text-sm hover:bg-primary-hover transition-colors"
              >
                Ver mis turnos en Mi Cuenta
              </button>
              <button
                onClick={() => {
                  setStep(1);
                  setFecha('');
                  setSelectedHora('');
                }}
                className="px-6 py-3.5 rounded-xl border border-neutral-200 text-neutral-700 font-semibold text-sm hover:bg-neutral-50 transition-colors"
              >
                Agendar otro turno
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
