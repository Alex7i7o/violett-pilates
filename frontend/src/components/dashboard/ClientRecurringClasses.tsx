import React from 'react';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { type Recurrencia } from '../../hooks/useClientProfile';

interface ClientRecurringClassesProps {
  recurrencias: Recurrencia[] | undefined;
  onCancelClick: (id: string) => void;
}

export function ClientRecurringClasses({ recurrencias, onCancelClick }: ClientRecurringClassesProps) {
  if (!recurrencias || recurrencias.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-foreground">Mi Horario Fijo / Recurrente</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {recurrencias.map(rec => {
          const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábados', 'Domingos'];
          const dayName = days[rec.dia_semana - 1];
          return (
            <Card key={rec.id} className="bg-violett-50/50 relative overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                  <Badge variant="secondary">Fijo Semanal</Badge>
                  <button 
                    onClick={() => onCancelClick(rec.id)}
                    className="text-sm font-medium text-red-500 hover:text-red-700 transition-colors"
                  >
                    Baja definitiva
                  </button>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xl font-bold text-foreground mb-1">{rec.classType}</p>
                <p className="text-muted text-sm">Todos los {dayName}</p>
                <p className="text-muted text-sm font-medium">⏰ {rec.time} hs</p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
