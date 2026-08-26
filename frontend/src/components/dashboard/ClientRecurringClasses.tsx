import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { type Recurrencia } from '../../hooks/useClientProfile';

interface ClientRecurringClassesProps {
  recurrencias: Recurrencia[] | undefined;
  onCancelClick: (id: string) => void;
}

export function ClientRecurringClasses({ recurrencias, onCancelClick }: ClientRecurringClassesProps) {
  if (!recurrencias) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-foreground">Mi Horario Fijo / Recurrente</h2>
      {recurrencias.length === 0 ? (
        <Card className="bg-white/50 border-dashed border-2">
          <CardContent className="p-6 text-center text-muted">
            No tienes horarios fijos asignados actualmente.
          </CardContent>
        </Card>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative min-h-[140px]">
        <AnimatePresence mode="popLayout">
          {recurrencias.map(rec => {
          const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábados', 'Domingos'];
          const dayName = days[rec.dia_semana - 1];
          return (
            <motion.div
              layout
              key={rec.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ type: "spring", bounce: 0, duration: 0.5 }}
            >
              <Card className="bg-violett-50/50 h-full relative overflow-hidden">
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
            </motion.div>
          );
        })}
        </AnimatePresence>
      </div>
      )}
    </div>
  );
}
