import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { type ProfesorDashboardData } from '../../types/profesor';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  data: ProfesorDashboardData;
  formatFecha: (f: string) => string;
}

export function ProfesorTabHoy({ data, formatFecha }: Props) {
  return (
    <motion.div key="hoy" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
      <section>
        <h3 className="text-xl font-bold text-foreground mb-4">Clases de Hoy</h3>
        {data.turnos_hoy.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted">
              No tienes clases programadas para hoy.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {data.turnos_hoy.map((t) => (
              <Card key={t.id} className="relative overflow-hidden">
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
            ))}
          </div>
        )}
      </section>
    </motion.div>
  );
}
