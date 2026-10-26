import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  AlertCircle, ArrowRight, Calendar, Sparkles, ChevronDown, 
  Clock, CheckCircle2, X, ChevronRight, BookmarkCheck
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookingGrid } from '../../components/booking/BookingGrid';
import { useClientProfile } from '../../hooks/useClientProfile';
import { useBookings, type Turno } from '../../hooks/useBookings';
import { ResenaWidget } from '../../../../plugins/resenas/frontend/ResenaWidget';
import { Modal } from '../../components/ui/Modal';
import { CancelModal } from '../../components/booking/CancelModal';

export function InicioView() {
  const { profile } = useClientProfile();
  const { turnos, loading, bookTurno, cancelTurno } = useBookings();

  // Estados para modales y acordeón
  const [showUpcomingModal, setShowUpcomingModal] = useState(false);
  const [selectedTurnoToCancel, setSelectedTurnoToCancel] = useState<Turno | null>(null);
  const [isAgendaOpen, setIsAgendaOpen] = useState(false);

  // Clases agendadas de la alumna
  const upcomingBookings = turnos.filter(t => t.isBookedByMe);

  const formatUpcomingDate = (dateStr: string, timeStr?: string) => {
    try {
      const datePart = (dateStr || '').split('T')[0];
      const [year, month, day] = datePart.split('-').map(Number);
      const date = new Date(year, month - 1, day);
      if (isNaN(date.getTime())) return dateStr || 'Fecha a confirmar';
      const DIAS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
      const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
      const horaStr = timeStr ? ` a las ${timeStr.slice(0, 5)} hs` : '';
      return `${DIAS[date.getDay()]} ${day} de ${MESES[date.getMonth()]}${horaStr}`;
    } catch (e) {
      return dateStr;
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 md:px-0 pt-4 md:pt-0 pb-10 space-y-6">
      {/* HEADER DE SALUDO Y BADGES */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-1 mb-2">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight font-sans">
            Hola, {profile?.nombre?.split(' ')[0] || profile?.name?.split(' ')[0] || 'Alumna'}
          </h1>
          <p className="text-muted text-xs md:text-sm mt-0.5">Encontrá y reservá tu próxima clase</p>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
          {/* BADGE 1: CLASES POR TOMAR (AGENDADAS) - CLICKEABLE CON MODAL */}
          <button
            type="button"
            onClick={() => setShowUpcomingModal(true)}
            className="px-3 sm:px-4 py-1.5 sm:py-2 rounded-2xl border border-primary-main/20 bg-primary-light/70 text-primary-main hover:bg-primary-light hover:border-primary-main/40 hover:shadow-xs active:scale-95 transition-all flex items-center gap-2 sm:gap-2.5 shadow-2xs group text-left cursor-pointer"
            title="Tocá para ver el detalle de tus clases agendadas"
          >
            <div className="w-2 h-2 sm:w-2.5 sm:h-2.5 rounded-full bg-primary-main animate-pulse shrink-0" />
            <div className="flex flex-col">
              <span className="text-[9px] sm:text-[10px] uppercase font-bold tracking-wider text-primary-main/80 leading-none">
                Clases por tomar
              </span>
              <span className="text-xs sm:text-sm font-extrabold leading-tight mt-0.5 text-primary-main flex items-center gap-1">
                {upcomingBookings.length} {upcomingBookings.length === 1 ? 'agendada' : 'agendadas'}
                <span className="text-[10px] opacity-70 group-hover:translate-x-0.5 transition-transform">↗</span>
              </span>
            </div>
          </button>

          {/* BADGE 2: CUPOS PARA AGENDAR DISPONIBLES */}
          {profile && (
            <div className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-2xl border flex items-center gap-2 sm:gap-2.5 shadow-2xs shrink-0 transition-all ${
              (profile.remainingClasses || 0) > 0
                ? 'bg-emerald-50/90 border-emerald-200 text-emerald-950'
                : 'bg-amber-50/90 border-amber-200 text-amber-950'
            }`}>
              <div className={`w-2 h-2 sm:w-2.5 sm:h-2.5 rounded-full shrink-0 ${
                (profile.remainingClasses || 0) > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
              }`} />
              <div className="flex flex-col text-left">
                <span className="text-[9px] sm:text-[10px] uppercase font-bold tracking-wider text-muted-foreground opacity-75 leading-none">
                  Cupos para agendar
                </span>
                <span className="text-xs sm:text-sm font-extrabold leading-tight mt-0.5">
                  {profile.remainingClasses ?? 0} {profile.remainingClasses === 1 ? 'disponible' : 'disponibles'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ALERTA DE PERFIL INCOMPLETO */}
      {profile?.perfil_incompleto && (
        <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-300 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-700 flex items-center justify-center shrink-0">
              <AlertCircle className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-sm font-bold text-amber-950">¡Completá tus datos de alumna!</p>
              <p className="text-xs text-amber-900/80 mt-0.5">
                Para tu ficha médica y seguridad, por favor completá tus datos personales pendientes.
              </p>
            </div>
          </div>
          <Link 
            to="/perfil"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold shadow-sm transition-colors whitespace-nowrap self-end sm:self-center"
          >
            Actualizar datos
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* SECCIÓN PREVIA A LA AGENDA: ESTADO DEL PLAN Y CLASES FIJAS */}
      <div className="bg-gradient-to-br from-white via-white to-primary-light/25 rounded-3xl border border-neutral-200/80 p-5 sm:p-6 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-neutral-100">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-2xl bg-primary-light/80 text-primary-main flex items-center justify-center font-bold">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-foreground font-sans">
                Tu Abono y Clases Fijas
              </h2>
              <p className="text-xs text-muted">
                Tus horarios reservados fijos y las clases que te quedan del plan
              </p>
            </div>
          </div>

          {(profile?.remainingClasses || 0) > 0 && (
            <button
              type="button"
              onClick={() => setIsAgendaOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary-main text-white hover:bg-primary-hover text-xs font-semibold shadow-2xs transition-colors self-start sm:self-auto cursor-pointer"
            >
              <span>+ Agendar otra clase</span>
            </button>
          )}
        </div>

        {/* GRID DE ESTADO DE PLAN Y CLASES FIJAS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* BLOQUE A: ESTADO DEL PLAN */}
          <div className="bg-white/95 border border-neutral-200/70 rounded-2xl p-4 shadow-2xs space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] sm:text-[11px] uppercase font-bold tracking-wider text-muted font-mono">
                  Membresía
                </span>
                <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                  (profile?.remainingClasses || 0) > 0
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border-amber-200'
                }`}>
                  {(profile?.remainingClasses || 0) > 0 ? '✦ Activo' : 'Sin créditos libres'}
                </span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold font-laluxes text-primary-main">
                {profile?.activePlan || 'Sin plan activo'}
              </h3>
            </div>

            <div className="space-y-2 pt-2 border-t border-neutral-100">
              <div className="flex items-baseline justify-between text-xs">
                <span className="text-neutral-500 font-medium">Clases disponibles para agendar:</span>
                <span className="text-sm sm:text-base font-bold text-foreground">
                  {profile?.remainingClasses ?? 0} {profile?.totalClasses ? <span className="text-xs font-normal text-muted">/ {profile.totalClasses} totales</span> : ''}
                </span>
              </div>

              <div className="flex items-baseline justify-between text-xs">
                <span className="text-neutral-500 font-medium">Clases agendadas por tomar:</span>
                <button
                  type="button"
                  onClick={() => setShowUpcomingModal(true)}
                  className="text-primary-main font-bold hover:underline inline-flex items-center gap-1 cursor-pointer"
                >
                  {upcomingBookings.length} {upcomingBookings.length === 1 ? 'clase' : 'clases'} ↗
                </button>
              </div>

              {profile?.expirationDate && profile.expirationDate !== '-' && (
                <div className="flex items-baseline justify-between text-[11px] text-neutral-400 pt-1">
                  <span>Vencimiento del período:</span>
                  <span>{profile.expirationDate} ({profile.daysUntilExpiration ?? 0} días)</span>
                </div>
              )}
            </div>
          </div>

          {/* BLOQUE B: CLASES FIJAS SEMANALES */}
          <div className="bg-white/95 border border-neutral-200/70 rounded-2xl p-4 shadow-2xs space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] sm:text-[11px] uppercase font-bold tracking-wider text-muted font-mono">
                  Horarios Semanales
                </span>
                <span className="text-[11px] font-semibold text-neutral-600 bg-neutral-100 px-2 py-0.5 rounded-full">
                  {profile?.recurrencias?.length || 0} {profile?.recurrencias?.length === 1 ? 'fijo' : 'fijos'}
                </span>
              </div>
              <h3 className="text-lg font-bold text-foreground">
                Tus Clases Fijas
              </h3>
            </div>

            <div className="pt-2 border-t border-neutral-100 flex-1">
              {profile?.recurrencias && profile.recurrencias.length > 0 ? (
                <div className="space-y-2">
                  {profile.recurrencias.map(rec => {
                    const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
                    const dayName = days[rec.dia_semana - 1] || 'Día';
                    const hora = rec.hora_inicio?.slice(0, 5) || rec.hora_inicio;
                    return (
                      <div
                        key={rec.id}
                        className="flex items-center justify-between p-2.5 rounded-xl bg-primary-light/40 border border-primary-light"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-primary-main text-white flex items-center justify-center font-bold text-xs shrink-0">
                            ✦
                          </div>
                          <div>
                            <span className="text-xs font-bold text-foreground block">
                              Todos los {dayName} a las {hora} hs
                            </span>
                            <span className="text-[11px] text-muted block">
                              {rec.clase_nombre || 'Pilates Reformer'}
                            </span>
                          </div>
                        </div>
                        <span className="text-[10px] font-bold text-primary-main bg-white px-2 py-0.5 rounded-full border border-primary-main/20 shrink-0">
                          Fijo Semanal
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-neutral-50 border border-dashed border-neutral-200 text-xs text-neutral-500 space-y-1">
                  <p className="font-semibold text-neutral-700">Sin horarios fijos asignados</p>
                  <p className="text-[11px] text-neutral-500 leading-relaxed">
                    Reservás tus clases de manera puntual. Si querés fijar días y horarios fijos semanales para no tener que agendar manualmente, consultá con recepción.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* TOGGLE ACORDEÓN: AGENDA DISPONIBLE */}
      <div className="bg-white rounded-3xl border border-neutral-200/80 shadow-xs overflow-hidden transition-all">
        <button
          type="button"
          onClick={() => setIsAgendaOpen(!isAgendaOpen)}
          className="w-full p-4 sm:p-5 flex items-center justify-between text-left hover:bg-neutral-50/60 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-primary-light/70 text-primary-main flex items-center justify-center shrink-0">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold text-foreground font-sans">Agenda Disponible</h2>
                <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-primary-light/60 text-primary-main border border-primary-main/15">
                  Reservar turnos
                </span>
              </div>
              <p className="text-xs text-muted mt-0.5">
                {isAgendaOpen 
                  ? 'Tocá para plegar los horarios disponibles' 
                  : 'Tocá para desplegar los días y horarios libres para agendar'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <span className="hidden sm:inline-block text-xs font-semibold text-primary-main">
              {isAgendaOpen ? 'Ocultar horarios' : 'Ver horarios disponibles'}
            </span>
            <div className={`w-8 h-8 rounded-full bg-neutral-100 flex items-center justify-center text-neutral-600 transition-transform duration-300 ${isAgendaOpen ? 'rotate-180 bg-primary-light/60 text-primary-main' : ''}`}>
              <ChevronDown size={18} />
            </div>
          </div>
        </button>

        <AnimatePresence initial={false}>
          {isAgendaOpen && (
            <motion.div
              key="agenda-content"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.35, ease: 'easeInOut' }}
              className="overflow-hidden border-t border-neutral-100"
            >
              <div className="p-4 sm:p-6">
                <BookingGrid 
                  turnos={turnos}
                  loading={loading}
                  onBook={bookTurno}
                  onCancel={cancelTurno}
                  hideTitle={true}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* MODAL DE CLASES POR TOMAR (AGENDADAS) */}
      <Modal
        isOpen={showUpcomingModal}
        onClose={() => setShowUpcomingModal(false)}
        title="Mis Clases Agendadas"
        className="sm:max-w-xl"
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-2xl bg-primary-light/40 border border-primary-light text-xs text-primary-main">
            <span className="font-semibold">
              Tenés {upcomingBookings.length} {upcomingBookings.length === 1 ? 'clase programada' : 'clases programadas'}
            </span>
            <span className="text-[11px] text-neutral-500">
              Gral. Guido 1573, Ramos Mejía
            </span>
          </div>

          {upcomingBookings.length === 0 ? (
            <div className="py-8 text-center text-muted text-sm space-y-2">
              <Calendar className="w-10 h-10 text-neutral-300 mx-auto stroke-[1.5]" />
              <p className="font-semibold text-neutral-700">No tenés clases agendadas en este momento.</p>
              <p className="text-xs text-neutral-400">
                Podés desplegar la agenda abajo para elegir día y horario.
              </p>
              <button
                type="button"
                onClick={() => {
                  setShowUpcomingModal(false);
                  setIsAgendaOpen(true);
                }}
                className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary-main text-white text-xs font-semibold hover:bg-primary-hover transition"
              >
                Ver agenda disponible
              </button>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[60vh] overflow-y-auto custom-scrollbar pr-1">
              {upcomingBookings.map(turno => (
                <div
                  key={turno.id}
                  className="p-3.5 rounded-2xl border border-neutral-200/90 bg-white shadow-2xs flex items-center justify-between gap-3 hover:border-primary-main/30 transition-colors"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-foreground truncate">
                        {formatUpcomingDate(turno.date)}
                      </span>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        turno.isRecurring
                          ? 'bg-primary-light text-primary-main border border-primary-main/15'
                          : 'bg-neutral-100 text-neutral-700'
                      }`}>
                        {turno.isRecurring ? 'Clase fija ✦' : 'Puntual'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted">
                      <span className="font-semibold text-primary-main">⏰ {turno.time} hs</span>
                      <span>•</span>
                      <span className="truncate">{turno.classType}</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setSelectedTurnoToCancel(turno)}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold text-rose-600 hover:bg-rose-50 border border-rose-200/60 active:scale-95 transition-all shrink-0 cursor-pointer"
                  >
                    Cancelar
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="pt-3 border-t border-neutral-100 flex items-center justify-between text-xs text-neutral-400">
            <span>Violett Pilates Boutique</span>
            <button
              type="button"
              onClick={() => setShowUpcomingModal(false)}
              className="px-4 py-2 rounded-xl bg-neutral-100 hover:bg-neutral-200 text-neutral-700 font-semibold transition cursor-pointer"
            >
              Cerrar
            </button>
          </div>
        </div>
      </Modal>

      {/* MODAL DE CONFIRMACIÓN DE CANCELACIÓN */}
      <CancelModal
        isOpen={Boolean(selectedTurnoToCancel)}
        onClose={() => setSelectedTurnoToCancel(null)}
        turno={selectedTurnoToCancel}
        onConfirm={async (turnoId) => {
          await cancelTurno(turnoId);
          setSelectedTurnoToCancel(null);
        }}
      />

      <ResenaWidget />
    </div>
  );
}
