import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { type Turno } from '../../hooks/useBookings';

interface ClientUpcomingClassesProps {
  turnos: Turno[];
  onCancelClick: (turno: Turno) => void;
  hasRecurring?: boolean;
  contactPhone?: string;
}

export function ClientUpcomingClasses({ turnos, onCancelClick, hasRecurring, contactPhone }: ClientUpcomingClassesProps) {
  const myUpcomingBookings = turnos.filter(t => t.isBookedByMe);

  const formatUpcomingDate = (dateStr: string) => {
    try {
      const datePart = dateStr.split('T')[0];
      const [year, month, day] = datePart.split('-').map(Number);
      const date = new Date(year, month - 1, day);
      if (isNaN(date.getTime())) return 'Fecha inválida';
      const DIAS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
      const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
      return `${DIAS[date.getDay()]} ${day} ${MESES[date.getMonth()]}`;
    } catch(e) {
      return 'Fecha inválida';
    }
  };

  if (myUpcomingBookings.length === 0) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-foreground">Mis Próximas Clases Confirmadas</h2>
        {hasRecurring ? (
          <div className="bg-amber-50/90 border border-amber-200/90 rounded-2xl p-5 md:p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 text-xs font-bold uppercase tracking-wider">
                  <span>✦</span> Renovación de Clases Fijas
                </div>
                <h3 className="text-base font-bold text-amber-950">¡Completaste tus clases fijas de este período!</h3>
                <p className="text-xs sm:text-sm text-amber-900/80 leading-relaxed max-w-xl">
                  Tus clases agendadas de este mes ya finalizaron. Para que tus clases se vuelvan a agendar de manera automática para el próximo ciclo en tu horario fijo habitual, recordá abonar tu plan en recepción.
                </p>
              </div>
              {contactPhone && (
                <a 
                  href={`https://wa.me/${contactPhone}?text=${encodeURIComponent("Hola! Quisiera abonar mi cuota para renovar mis clases fijas.")}`}
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="shrink-0 bg-primary-main hover:bg-primary-hover text-white text-xs font-bold px-4 py-2.5 rounded-xl transition-all shadow-sm"
                >
                  Consultar / Abonar
                </a>
              )}
            </div>
          </div>
        ) : (
          <div className="p-6 text-center bg-white/40 border border-dashed border-primary-light rounded-2xl text-muted text-sm">
            No tienes próximas clases agendadas en este momento.
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-foreground">Mis Próximas Clases Confirmadas</h2>
      <div className="flex gap-3 overflow-x-auto pb-4 snap-x relative min-h-[160px]">
        <AnimatePresence mode="wait">
          {myUpcomingBookings.map(turno => (
            <motion.div
              layout
              key={turno.id}
              initial={{ opacity: 0, scale: 0.9, x: 20 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.9, x: -20 }}
              transition={{ type: "spring", bounce: 0, duration: 0.5 }}
              className="min-w-[280px] snap-start"
            >
              <Card className="h-full relative overflow-hidden">
            <CardHeader className="pb-2">
              <Badge className="w-fit" variant={turno.isRecurring ? "secondary" : "default"}>
                {turno.isRecurring ? "Clase fija" : "Puntual"}
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-end">
                <div>
                  <p className="text-lg font-bold text-foreground mb-1">{formatUpcomingDate(turno.date)}</p>
                  <p className="text-primary-main font-semibold mb-1">⏰ {turno.time} hs</p>
                  <p className="text-muted text-sm font-medium">{turno.classType}</p>
                </div>
                <button 
                  onClick={() => onCancelClick(turno)}
                  className="text-sm font-medium text-red-500 hover:text-red-700 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </CardContent>
            </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
