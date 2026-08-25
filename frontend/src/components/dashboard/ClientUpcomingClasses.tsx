import React from 'react';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { type Turno } from '../../hooks/useBookings';

interface ClientUpcomingClassesProps {
  turnos: Turno[];
  onCancelClick: (turno: Turno) => void;
}

export function ClientUpcomingClasses({ turnos, onCancelClick }: ClientUpcomingClassesProps) {
  const myUpcomingBookings = turnos.filter(t => t.isBookedByMe);

  if (myUpcomingBookings.length === 0) {
    return null;
  }

  const formatUpcomingDate = (dateStr: string) => {
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    const weekdayFormatter = new Intl.DateTimeFormat('es-AR', { weekday: 'long' });
    const weekday = weekdayFormatter.format(date);
    const capitalizedWeekday = weekday.charAt(0).toUpperCase() + weekday.slice(1);
    const dayAndMonth = new Intl.DateTimeFormat('es-AR', { day: 'numeric', month: 'short' }).format(date);
    return `${capitalizedWeekday} ${dayAndMonth}`;
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-foreground">Mis Próximas Clases Confirmadas</h2>
      <div className="flex gap-3 overflow-x-auto pb-4 snap-x">
        {myUpcomingBookings.map(turno => (
          <Card key={turno.id} className="min-w-[280px] snap-start relative overflow-hidden">
            <CardHeader className="pb-2">
              <Badge className="w-fit" variant={turno.isRecurring ? "secondary" : "default"}>
                {turno.isRecurring ? "Clase fija" : "Puntual"}
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-end">
                <div>
                  <p className="text-xl font-bold text-foreground mb-1">{turno.classType}</p>
                  <p className="text-muted text-sm">{formatUpcomingDate(turno.date)}</p>
                  <p className="text-muted text-sm font-medium">⏰ {turno.time} hs</p>
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
        ))}
      </div>
    </div>
  );
}
