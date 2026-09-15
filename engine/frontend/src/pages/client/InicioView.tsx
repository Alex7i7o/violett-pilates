import React from 'react';
import { BookingGrid } from '../../components/booking/BookingGrid';
import { useClientProfile } from '../../hooks/useClientProfile';
import { useBookings } from '../../hooks/useBookings';
import { ResenaWidget } from '../../../../plugins/resenas/frontend/ResenaWidget';

export function InicioView() {
  const { profile } = useClientProfile();
  const { turnos, loading, bookTurno, cancelTurno } = useBookings();

  return (
    <div className="w-full max-w-5xl mx-auto px-4 md:px-0 pt-4 md:pt-0 pb-6 space-y-6">
      <div className="md:hidden mt-2 mb-6">
        <h1 className="text-3xl font-bold text-foreground">Hola, {profile?.nombre?.split(' ')[0] || ''}</h1>
        <p className="text-muted text-sm mt-1">Encontrá tu próxima clase</p>
      </div>

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
