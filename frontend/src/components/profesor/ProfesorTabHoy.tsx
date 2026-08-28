import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { FeedbackButton } from '../ui/FeedbackButton';
import { api } from '../../lib/api';
import { toast } from 'sonner';
import { useState } from 'react';
import { type ProfesorDashboardData } from '../../types/profesor';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  data: ProfesorDashboardData;
  formatFecha: (f: string) => string;
}

export function ProfesorTabHoy({ data, formatFecha }: Props) {
  const [localData, setLocalData] = useState(data);
  const [expandedIds, setExpandedIds] = useState<string[]>([]);

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const handleAsistencia = async (reservaId: number, estado: 'TOMADA' | 'AUSENTE' | 'CONFIRMADA') => {
    try {
      await api.put(`/profesor/reservas/${reservaId}/asistencia/`, { estado });
      toast.success('Asistencia actualizada');
      
      // Update local state
      setLocalData(prev => {
        const newData = { ...prev };
        newData.turnos_hoy = newData.turnos_hoy.map(turno => {
          return {
            ...turno,
            reservas_list: turno.reservas_list?.map((res: any) => 
              res.id === reservaId ? { ...res, estado } : res
            )
          };
        });
        return newData;
      });
    } catch (e) {
      toast.error('Error al actualizar asistencia');
      console.error(e);
    }
  };
  return (
    <motion.div key="hoy" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
      <section>
        <h3 className="text-xl font-bold text-foreground mb-4">Clases de Hoy</h3>
        {localData.turnos_hoy.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted">
              No tienes clases programadas para hoy.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {localData.turnos_hoy.map((t) => (
              <Card key={t.id} className="relative overflow-hidden transition-all duration-300 hover:border-violett-300">
                <CardContent className="p-0">
                  {/* Header clickeable */}
                  <div 
                    className="p-4 cursor-pointer flex justify-between items-center bg-white hover:bg-violett-50/50 transition-colors"
                    onClick={() => toggleExpand(t.id)}
                  >
                    <div>
                      <p className="font-bold text-foreground">{formatFecha(t.fecha)}</p>
                      <p className="text-muted text-sm">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)} hs</p>
                    </div>
                    <div className="text-right flex items-center gap-4">
                      <div>
                        <p className="text-violett-900 font-medium">{t.clase_nombre}</p>
                        <Badge variant="secondary" className="mt-1">{t.reservas_list?.length || 0} inscriptas</Badge>
                      </div>
                      <div className="text-violett-400">
                        <svg className={`w-5 h-5 transform transition-transform ${expandedIds.includes(t.id) ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/></svg>
                      </div>
                    </div>
                  </div>
                  
                  {/* Lista de Alumnos Desplegable */}
                  <AnimatePresence>
                    {expandedIds.includes(t.id) && (
                      <motion.div 
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="p-4 pt-0 border-t border-violett-100 bg-violett-50/20">
                          <h4 className="text-sm font-bold text-violett-900 mb-3 mt-4">Asistencia de la Clase</h4>
                          {(!t.reservas_list || t.reservas_list.length === 0) ? (
                            <p className="text-sm text-muted">No hay alumnas inscriptas a esta clase.</p>
                          ) : (
                            <div className="space-y-3">
                              {t.reservas_list.map((res: any) => (
                                <div key={res.id} className="flex flex-col sm:flex-row justify-between sm:items-center p-3 bg-white border border-violett-100 shadow-sm rounded-xl transition-all">
                                  <div>
                                    <p className="font-medium text-foreground">{res.alumno_nombre} {res.alumno_apellido}</p>
                                    <Badge variant="outline" className="mt-1 text-xs">
                                      {res.estado === 'TOMADA' ? 'Presente' : res.estado === 'AUSENTE' ? 'Ausente' : 'Inscripta'}
                                    </Badge>
                                  </div>
                                  <motion.div layout className="flex gap-2 mt-3 sm:mt-0 w-full sm:w-[220px]">
                                                                          <AnimatePresence initial={false}>
                                        {(res.estado === 'CONFIRMADA' || res.estado === 'TOMADA') && (
                                          <motion.div 
                                            key="presente"
                                            layout
                                            initial={{ opacity: 0, flex: 0 }} 
                                            animate={{ opacity: 1, flex: res.estado === 'TOMADA' ? '1 1 100%' : '1 1 50%' }} 
                                            exit={{ opacity: 0, flex: 0, padding: 0, margin: 0, overflow: 'hidden' }} 
                                            transition={{ type: 'spring', bounce: 0, duration: 0.6 }}
                                            className="flex"
                                          >
                                            <FeedbackButton 
                                              size="sm" 
                                              variant={res.estado === 'TOMADA' ? 'default' : 'outline'}
                                                key={`presente-btn-${res.estado}`}
                                              onClick={() => handleAsistencia(res.id, res.estado === 'TOMADA' ? 'CONFIRMADA' : 'TOMADA')}
                                              className={res.estado !== 'TOMADA' ? "w-full flex-1 whitespace-nowrap bg-white hover:bg-violett-50 text-violett-900 border-violett-200 hover:border-violett-300" : "w-full flex-1 whitespace-nowrap bg-violett-900 hover:bg-violett-800 border-violett-900 text-white"}
                                              initialText={res.estado === 'TOMADA' ? '✓ Presente (Deshacer)' : 'Presente'}
                                              successText={res.estado === 'TOMADA' ? 'Deshecho' : 'Asistió'}
                                            />
                                          </motion.div>
                                        )}
                                        {(res.estado === 'CONFIRMADA' || res.estado === 'AUSENTE') && (
                                          <motion.div 
                                            key="ausente"
                                            layout
                                            initial={{ opacity: 0, flex: 0 }} 
                                            animate={{ opacity: 1, flex: res.estado === 'AUSENTE' ? '1 1 100%' : '1 1 50%' }} 
                                            exit={{ opacity: 0, flex: 0, padding: 0, margin: 0, overflow: 'hidden' }} 
                                            transition={{ type: 'spring', bounce: 0, duration: 0.6 }}
                                            className="flex"
                                          >
                                            <FeedbackButton 
                                              size="sm" 
                                              variant={res.estado === 'AUSENTE' ? 'destructive' : 'outline'}
                                                key={`ausente-btn-${res.estado}`}
                                              onClick={() => handleAsistencia(res.id, res.estado === 'AUSENTE' ? 'CONFIRMADA' : 'AUSENTE')}
                                              className={res.estado !== 'AUSENTE' ? "w-full flex-1 whitespace-nowrap bg-white hover:bg-rose-50 text-rose-500 border-rose-200 hover:border-rose-300" : "w-full flex-1 whitespace-nowrap text-white bg-rose-500 hover:bg-rose-600 border-rose-500"}
                                              initialText={res.estado === 'AUSENTE' ? '✗ Ausente (Deshacer)' : 'Ausente'}
                                              successText={res.estado === 'AUSENTE' ? 'Deshecho' : 'Faltó'}
                                            />
                                          </motion.div>
                                        )}
                                      </AnimatePresence>
                                  </motion.div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </motion.div>
  );
}
