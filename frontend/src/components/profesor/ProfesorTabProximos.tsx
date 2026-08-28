import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { type ProfesorDashboardData } from '../../types/profesor';
import { motion } from 'framer-motion';

interface Props {
  data: ProfesorDashboardData;
  formatFecha: (f: string) => string;
  showPast: boolean;
  setShowPast: (val: boolean) => void;
}

export function ProfesorTabProximos({ data, formatFecha, showPast, setShowPast }: Props) {
  const displayedTurnos = showPast 
    ? data.turnos_semana 
    : data.turnos_semana.filter(t => new Date(`${t.fecha}T${t.hora_inicio}`) >= new Date());

  return (
    <motion.div key="proximos" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
      <section>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-foreground">Próximos Días</h3>
          <Button variant="outline" size="sm" onClick={() => setShowPast(!showPast)}>
            {showPast ? 'Ocultar pasadas' : 'Ver todas de la semana'}
          </Button>
        </div>
        {displayedTurnos.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted">
              No tienes clases programadas próximamente.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {displayedTurnos.map((t) => {
              const isPast = new Date(`${t.fecha}T${t.hora_inicio}`) < new Date();
              return (
                <Card key={t.id} className={`relative overflow-hidden ${isPast ? 'opacity-60 bg-gray-50/50' : ''}`}>
                  <CardContent className="flex justify-between items-center p-4">
                    <div>
                      <p className="font-bold text-foreground">{formatFecha(t.fecha)}</p>
                      <p className="text-muted text-sm">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)} hs</p>
                    </div>
                    <div className="text-right">
                      <p className="text-violett-900 font-medium">{t.clase_nombre}</p>
                      <Badge variant="secondary" className="mt-1">{t.estado}</Badge>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </section>
    </motion.div>
  );
}
