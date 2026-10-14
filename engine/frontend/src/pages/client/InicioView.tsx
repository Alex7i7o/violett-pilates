import React from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ArrowRight } from 'lucide-react';
import { BookingGrid } from '../../components/booking/BookingGrid';
import { useClientProfile } from '../../hooks/useClientProfile';
import { useBookings } from '../../hooks/useBookings';
import { ResenaWidget } from '../../../../plugins/resenas/frontend/ResenaWidget';

export function InicioView() {
  const { profile } = useClientProfile();
  const { turnos, loading, bookTurno, cancelTurno } = useBookings();

  return (
    <div className="w-full max-w-5xl mx-auto px-4 md:px-0 pt-4 md:pt-0 pb-6 space-y-6">
      <div className="flex items-center justify-between gap-3 mt-1 mb-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-foreground tracking-tight font-sans">
            Hola, {profile?.nombre?.split(' ')[0] || profile?.name?.split(' ')[0] || 'Alumna'}
          </h1>
          <p className="text-muted text-xs md:text-sm mt-0.5">Encontrá y reservá tu próxima clase</p>
        </div>

        {profile && (
          <div className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-2xl border flex items-center gap-2 sm:gap-2.5 shadow-sm shrink-0 transition-all ${
            (profile.remainingClasses || 0) > 0
              ? 'bg-emerald-50/90 border-emerald-200 text-emerald-950'
              : 'bg-amber-50/90 border-amber-200 text-amber-950'
          }`}>
            <div className={`w-2 h-2 sm:w-2.5 sm:h-2.5 rounded-full ${
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

      {profile?.perfil_incompleto && (
        <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-300 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
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
      
      

      <BookingGrid 
        turnos={turnos}
        loading={loading}
        onBook={bookTurno}
        onCancel={cancelTurno}
      />
      <ResenaWidget />
    </div>
  );
}

