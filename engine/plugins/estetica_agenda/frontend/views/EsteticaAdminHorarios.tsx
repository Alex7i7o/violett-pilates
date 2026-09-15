import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

export const EsteticaAdminHorarios = () => {
  const [dias, setDias] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const NOMBRES_DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

  useEffect(() => {
    api.get('/config-dias/')
      .then(res => {
        // Rellenar días que faltan
        const serverDias = res.data;
        const fullDias = NOMBRES_DIAS.map((nombre, index) => {
          const found = serverDias.find((d: any) => d.dia_semana === index);
          return found || {
            dia_semana: index,
            is_active: false,
            hora_apertura: '09:00:00',
            hora_cierre: '18:00:00',
            break_inicio: '',
            break_fin: ''
          };
        });
        setDias(fullDias);
      })
      .catch(() => toast.error('Error cargando horarios'))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (dia: any) => {
    try {
      if (dia.id) {
        await api.put(`/config-dias/${dia.id}/`, dia);
      } else {
        const res = await api.post('/config-dias/', dia);
        setDias(prev => prev.map(d => d.dia_semana === dia.dia_semana ? res.data : d));
      }
      toast.success(`Horario del ${NOMBRES_DIAS[dia.dia_semana]} guardado`);
    } catch (error) {
      toast.error('Error al guardar horario');
    }
  };

  if (loading) return <div className="p-8">Cargando...</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-primary-main mb-2">Configuración de Horarios</h1>
      <p className="text-neutral-500 mb-8">Configurá los días y horarios de atención de tu negocio.</p>
      
      <div className="grid gap-6 md:grid-cols-2">
        {dias.map(dia => (
          <div key={dia.dia_semana} className={`bg-white border rounded-2xl p-6 ${dia.is_active ? 'border-primary-main/20 shadow-sm' : 'border-neutral-200 opacity-60'}`}>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold">{NOMBRES_DIAS[dia.dia_semana]}</h2>
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer" 
                  checked={dia.is_active}
                  onChange={e => {
                    const newDias = [...dias];
                    newDias[dia.dia_semana].is_active = e.target.checked;
                    setDias(newDias);
                  }}
                />
                <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-main"></div>
              </label>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-xs font-semibold text-neutral-500 mb-1">Apertura</label>
                <input 
                  type="time" 
                  value={dia.hora_apertura} 
                  onChange={e => {
                    const newDias = [...dias];
                    newDias[dia.dia_semana].hora_apertura = e.target.value;
                    setDias(newDias);
                  }}
                  className="w-full p-2 border rounded-lg outline-none focus:border-primary-main"
                  disabled={!dia.is_active}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-neutral-500 mb-1">Cierre</label>
                <input 
                  type="time" 
                  value={dia.hora_cierre}
                  onChange={e => {
                    const newDias = [...dias];
                    newDias[dia.dia_semana].hora_cierre = e.target.value;
                    setDias(newDias);
                  }}
                  className="w-full p-2 border rounded-lg outline-none focus:border-primary-main"
                  disabled={!dia.is_active}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-xs font-semibold text-neutral-500 mb-1">Inicio Break</label>
                <input 
                  type="time" 
                  value={dia.break_inicio || ''} 
                  onChange={e => {
                    const newDias = [...dias];
                    newDias[dia.dia_semana].break_inicio = e.target.value;
                    setDias(newDias);
                  }}
                  className="w-full p-2 border rounded-lg outline-none focus:border-primary-main"
                  disabled={!dia.is_active}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-neutral-500 mb-1">Fin Break</label>
                <input 
                  type="time" 
                  value={dia.break_fin || ''} 
                  onChange={e => {
                    const newDias = [...dias];
                    newDias[dia.dia_semana].break_fin = e.target.value;
                    setDias(newDias);
                  }}
                  className="w-full p-2 border rounded-lg outline-none focus:border-primary-main"
                  disabled={!dia.is_active}
                />
              </div>
            </div>

            <button 
              onClick={() => handleSave(dia)}
              className="w-full py-3 bg-neutral-800 text-white rounded-xl font-medium hover:bg-neutral-900 transition-colors"
            >
              Guardar {NOMBRES_DIAS[dia.dia_semana]}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
