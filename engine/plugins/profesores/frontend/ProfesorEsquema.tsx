import React from 'react';
import { motion } from 'framer-motion';

export function ProfesorEsquema({ data, setPlantillaToAssign }: { data: any, setPlantillaToAssign: any }) {
  const { todas_plantillas, profesor_id } = data;

  const days = [
    { id: 1, name: 'Lunes' },
    { id: 2, name: 'Martes' },
    { id: 3, name: 'Miércoles' },
    { id: 4, name: 'Jueves' },
    { id: 5, name: 'Viernes' },
    { id: 6, name: 'Sábado' },
    { id: 7, name: 'Domingo' }
  ];

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h2 className="text-2xl font-light text-foreground uppercase tracking-widest font-laluxes">ESQUEMA GENERAL</h2>
        <p className="text-muted mt-2 text-sm max-w-2xl">
          Visualizá el esqueleto semanal completo. Las clases sin profesor asignado están marcadas en naranja y podés tomarlas.
        </p>
      </div>

      <div className="flex overflow-x-auto pb-6 -mx-4 px-4 custom-scrollbar snap-x">
        <div className="flex gap-4 lg:grid lg:grid-cols-7 lg:gap-6 min-w-max lg:min-w-0 w-full">
          {days.map(day => {
            const plantillasDia = todas_plantillas?.filter((p: any) => p.dia_semana === day.id).sort((a: any, b: any) => a.hora_inicio.localeCompare(b.hora_inicio)) || [];
            
            return (
              <div key={day.id} className="w-72 lg:w-auto snap-start shrink-0">
                <div className="bg-white/40 border border-primary-light/50 backdrop-blur-md text-center py-3 rounded-2xl mb-4 sticky top-0 z-10 shadow-sm">
                  <h3 className="font-bold text-primary-main tracking-wide">{day.name}</h3>
                </div>
                
                <div className="space-y-3">
                  {plantillasDia.length === 0 ? (
                    <div className="p-4 border border-dashed border-gray-200 rounded-2xl text-center">
                      <p className="text-xs text-muted italic">Sin clases</p>
                    </div>
                  ) : (
                    plantillasDia.map((p: any) => {
                      const isMine = p.profesor_id === profesor_id;
                      const isUnassigned = !p.profesor_id;

                      let cardClasses = "p-4 rounded-2xl border transition-all cursor-default shadow-sm relative overflow-hidden ";
                      
                      if (isMine) {
                        cardClasses += "bg-white border-primary-light";
                      } else if (isUnassigned) {
                        cardClasses += "bg-amber-50 border-amber-200 text-amber-800 shadow-amber-100/50";
                      } else {
                        // Someone else's
                        cardClasses += "bg-slate-50 border-slate-100 text-slate-500 opacity-60 grayscale-[50%]";
                      }

                      return (
                        <motion.div 
                          key={p.id}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          className={cardClasses}
                        >
                          {isUnassigned && (
                            <div className="absolute top-0 right-0 bg-amber-400 text-white text-[9px] font-bold px-2 py-0.5 rounded-bl-lg uppercase tracking-wider">
                              LIBRE
                            </div>
                          )}
                          {isMine && (
                            <div className="absolute top-0 right-0 bg-emerald-400 text-white text-[9px] font-bold px-2 py-0.5 rounded-bl-lg uppercase tracking-wider">
                              MÍA
                            </div>
                          )}

                          <p className="font-bold text-lg mb-1">{p.hora_inicio.slice(0,5)}</p>
                          <p className={`font-medium mb-1 ${isUnassigned ? 'text-amber-900' : isMine ? 'text-primary-hover' : ''}`}>{p.clase_nombre}</p>
                          
                          {isUnassigned && (
                            <button 
                              onClick={() => setPlantillaToAssign(p.id)}
                              className="mt-2 w-full py-1.5 px-3 bg-amber-500 hover:bg-amber-600 active:scale-95 transition-all text-white text-xs font-bold rounded-lg uppercase tracking-wider"
                            >
                              Tomar Horario
                            </button>
                          )}
                        </motion.div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
