import os

components_dir = "frontend/src/components/profesor"

prof_tab_proximos = """import React from 'react';
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
"""

prof_tab_recurrentes = """import React from 'react';
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
"""

prof_bolsa_trabajo = """import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { type ProfesorDashboardData } from '../../types/profesor';

interface Props {
  data: ProfesorDashboardData;
  setTurnoToAssign: (id: string) => void;
  setPlantillaToAssign: (id: string) => void;
  formatFecha: (f: string) => string;
}

export function ProfesorBolsaTrabajo({ data, setTurnoToAssign, setPlantillaToAssign, formatFecha }: Props) {
  const days = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábados','Domingos'];
  
  return (
    <div className="bg-violett-50/50 rounded-2xl p-6 border border-violett-100 sticky top-24 flex flex-col h-[calc(100vh-8rem)] shadow-sm">
      <div className="mb-4 flex-shrink-0">
        <h3 className="text-xl font-bold text-violett-900">Bolsa de Horarios</h3>
        <p className="text-muted text-sm mt-1">Clases que necesitan profesor</p>
        <hr className="mt-4 border-violett-200" />
      </div>
      
      <div className="flex-1 overflow-y-auto scrollbar-hide pr-2 space-y-6">
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-3 sticky top-0 bg-violett-50/90 backdrop-blur py-2 z-10">
            Horarios Fijos Disponibles
          </h4>
          {data.plantillas_libres.length === 0 ? (
            <p className="text-sm text-muted">No hay horarios fijos disponibles.</p>
          ) : (
            <div className="space-y-3">
              {data.plantillas_libres.map(p => (
                <Card key={p.id} className="border border-violett-100 shadow-sm">
                  <CardContent className="p-3">
                    <p className="font-semibold text-foreground">{days[p.dia_semana - 1]}s {p.hora_inicio.slice(0,5)}hs</p>
                    <p className="text-sm text-violett-900 font-medium">{p.clase_nombre}</p>
                    <Button size="sm" className="w-full mt-3" onClick={() => setPlantillaToAssign(p.id)}>
                      Tomar Fijo
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        <div>
          <h4 className="text-sm font-semibold text-foreground mb-3 sticky top-0 bg-violett-50/90 backdrop-blur py-2 z-10">
            Clases Puntuales Disponibles
          </h4>
          {data.turnos_libres.length === 0 ? (
            <p className="text-sm text-muted">No hay clases puntuales disponibles.</p>
          ) : (
            <div className="space-y-3">
              {data.turnos_libres.map(t => (
                <Card key={t.id} className="border border-violett-100 shadow-sm">
                  <CardContent className="p-3">
                    <p className="font-semibold text-foreground">{formatFecha(t.fecha)}</p>
                    <p className="text-sm text-muted">{t.hora_inicio.slice(0,5)}hs</p>
                    <p className="text-sm text-violett-900 font-medium">{t.clase_nombre}</p>
                    <Button size="sm" className="w-full mt-3" onClick={() => setTurnoToAssign(t.id)}>
                      Cubrir Clase
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
"""

with open(f"{components_dir}/ProfesorTabProximos.tsx", "w", encoding='utf-8') as f:
    f.write(prof_tab_proximos)

with open(f"{components_dir}/ProfesorTabRecurrentes.tsx", "w", encoding='utf-8') as f:
    f.write(prof_tab_recurrentes)

with open(f"{components_dir}/ProfesorBolsaTrabajo.tsx", "w", encoding='utf-8') as f:
    f.write(prof_bolsa_trabajo)

print("Created components Part 2")
