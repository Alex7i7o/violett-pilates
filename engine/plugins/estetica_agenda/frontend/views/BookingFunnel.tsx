import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/lib/api';
import { toast } from 'sonner';

export const BookingFunnel = () => {
  const [step, setStep] = useState(1);
  const [servicios, setServicios] = useState<any[]>([]);
  const [selectedServicio, setSelectedServicio] = useState<any>(null);
  
  const [fecha, setFecha] = useState<string>('');
  const [horarios, setHorarios] = useState<string[]>([]);
  const [selectedHora, setSelectedHora] = useState<string>('');
  
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get('/servicios/').then(res => setServicios(res.data)).catch(() => toast.error('Error cargando servicios'));
  }, []);

  useEffect(() => {
    if (fecha && selectedServicio) {
      setLoading(true);
      api.get(`/disponibilidad/?fecha=${fecha}&servicio_id=${selectedServicio.id}`)
        .then(res => {
          setHorarios(res.data);
        })
        .catch(() => toast.error('Error cargando horarios'))
        .finally(() => setLoading(false));
    }
  }, [fecha, selectedServicio]);

  const handleConfirm = async () => {
    try {
      setLoading(true);
      await api.post('/estetica-turnos/', {
        servicio: selectedServicio.id,
        fecha: fecha,
        hora_inicio: selectedHora,
        hora_fin: "00:00:00" // El backend debería auto-calcular esto en perform_create idealmente, o lo mandamos dummy
      });
      toast.success('¡¡Turno agendado con éééxito!');
      setStep(4);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Ocurrió un error al agendar.');
    } finally {
      setLoading(false);
    }
  };

  const fadeVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 }
  };

  return (
    <div className="w-full">
      <h1 className="text-3xl font-bold text-primary-main mb-8">Paso {step}: {
        step === 1 ? 'Elige un servicio' :
        step === 2 ? 'Elige el día y hora' :
        step === 3 ? 'Resumen de tu turno' : '¡Listo!'
      }</h1>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div key="step1" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="grid gap-4 sm:grid-cols-2">
            {servicios.map(srv => (
              <button 
                key={srv.id}
                onClick={() => { setSelectedServicio(srv); setStep(2); }}
                className="text-left p-6 rounded-2xl border-2 border-neutral-100 hover:border-primary-main hover:bg-primary-50 transition-all"
              >
                <h3 className="font-bold text-lg text-neutral-800">{srv.nombre}</h3>
                <p className="text-sm text-neutral-500 mt-1">{srv.duracion_minutos} min</p>
                <p className="font-semibold text-primary-main mt-3">${srv.precio_base}</p>
              </button>
            ))}
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="step2" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="space-y-6">
            <button onClick={() => setStep(1)} className="text-sm text-neutral-500 underline mb-4 inline-block">Volver a servicios</button>
            
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">Selecciona la fecha</label>
              <input 
                type="date" 
                value={fecha}
                onChange={e => setFecha(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                className="w-full p-4 rounded-xl border border-neutral-200 focus:border-primary-main focus:ring-1 focus:ring-primary-main outline-none transition-all"
              />
            </div>

            {fecha && (
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-3">Horarios disponibles</label>
                {loading ? <p className="text-sm text-neutral-500">Buscando horarios...</p> : (
                  <div className="flex flex-wrap gap-3">
                    {horarios.length === 0 ? <p className="text-sm text-neutral-500">No hay turnos para este día.</p> : horarios.map(hora => (
                      <button
                        key={hora}
                        onClick={() => { setSelectedHora(hora); setStep(3); }}
                        className="px-6 py-3 rounded-full font-medium text-sm border border-primary-main text-primary-main hover:bg-primary-main hover:text-white transition-colors"
                      >
                        {hora}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="step3" variants={fadeVariants} initial="hidden" animate="visible" exit="exit">
             <button onClick={() => setStep(2)} className="text-sm text-neutral-500 underline mb-6 inline-block">Cambiar fecha/hora</button>
             
             <div className="bg-neutral-50 p-6 rounded-2xl border border-neutral-100 mb-8">
               <h3 className="font-bold text-lg mb-4 text-neutral-800">Resumen de tu turno</h3>
               <div className="space-y-2 text-sm text-neutral-600">
                 <p><strong className="text-neutral-800">Servicio:</strong> {selectedServicio?.nombre}</p>
                 <p><strong className="text-neutral-800">Día:</strong> {fecha}</p>
                 <p><strong className="text-neutral-800">Hora:</strong> {selectedHora} hs</p>
                 <p><strong className="text-neutral-800">Precio:</strong> ${selectedServicio?.precio_base}</p>
               </div>
             </div>

             <button 
                onClick={handleConfirm} 
                disabled={loading}
                className="w-full py-4 rounded-xl bg-primary-main text-white font-bold text-lg hover:bg-primary-hover transition-colors disabled:opacity-50"
             >
                {loading ? 'Agendando...' : 'CONFIRMAR Y AGENDAR'}
             </button>
          </motion.div>
        )}

        {step === 4 && (
          <motion.div key="step4" variants={fadeVariants} initial="hidden" animate="visible" exit="exit" className="text-center py-12">
            <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6 text-4xl">✓</div>
            <h2 className="text-2xl font-bold text-neutral-800 mb-2">¡¡Turno Confirmado!</h2>
            <p className="text-neutral-500 mb-8">Te esperamos el {fecha} a las {selectedHora}.</p>
            <button onClick={() => { setStep(1); setFecha(''); setSelectedHora(''); }} className="text-primary-main font-medium underline">
              Agendar otro turno
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
