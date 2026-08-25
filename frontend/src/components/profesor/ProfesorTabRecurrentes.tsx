import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { type ProfesorDashboardData } from '../../types/profesor';
import { motion } from 'framer-motion';

interface Props {
  data: ProfesorDashboardData;
}

export function ProfesorTabRecurrentes({ data }: Props) {
  const days = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábados','Domingos'];
  return (
    <motion.div key="recurrentes" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
      <section>
        <h3 className="text-xl font-bold text-foreground mb-4">Mis Clases Recurrentes</h3>
        <p className="text-muted text-sm mb-4">
          Estas son las franjas horarias fijas que tienes asignadas. 
          Todas las semanas el sistema generará automáticamente estas clases bajo tu nombre.
        </p>
        {data.mis_plantillas.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted">
              No tienes horarios fijos asignados.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {data.mis_plantillas.map(p => (
              <Card key={p.id} className="relative overflow-hidden">
                <CardContent className="flex justify-between items-center p-4">
                  <div>
                    <Badge variant="secondary" className="mb-2 bg-violett-100 text-violett-900">Horario Fijo</Badge>
                    <p className="font-bold text-foreground">Todos los {days[p.dia_semana - 1]}</p>
                    <p className="text-muted text-sm">{p.hora_inicio.slice(0,5)} - {p.hora_fin.slice(0,5)} hs</p>
                  </div>
                  <div className="text-right">
                    <p className="text-violett-900 font-medium">{p.clase_nombre}</p>
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
