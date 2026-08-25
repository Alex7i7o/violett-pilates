import React from 'react';
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
