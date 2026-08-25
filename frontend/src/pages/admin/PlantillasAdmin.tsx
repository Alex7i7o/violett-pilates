import React, { useState, useEffect } from 'react';
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { toast } from "sonner";
import { api } from '../../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { motion, AnimatePresence } from 'framer-motion';

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

export function PlantillasAdmin() {
  const [plantillas, setPlantillas] = useState<any[]>([]);
  const [clases, setClases] = useState<any[]>([]);
  const [profesores, setProfesores] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [plantillaToDelete, setPlantillaToDelete] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    clase: '',
    profesor: '',
    dia_semana: '1',
    hora_inicio: '10:00',
    hora_fin: '11:00'
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [resPlantillas, resProfesores, resClases] = await Promise.all([
        api.get('/admin/plantillas/'),
        api.get('/admin/profesores/'),
        api.get('/admin/clases/')
      ]);
      setPlantillas(resPlantillas.data);
      setProfesores(resProfesores.data);
      setClases(resClases.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // For the sake of the example, if classes are not available we'll need to fetch them.
  const fetchClases = async () => {
    try {
        // Let's call admin/agenda to just extract unique clases if there is no endpoint?
        // Wait, Django Router has no Clases view. Let's add it quickly in backend or just use a raw input here?
        // Let's add it to backend if needed, but for now we'll do our best.
    } catch(e) {}
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        clase: formData.clase,
        dia_semana: parseInt(formData.dia_semana),
        hora_inicio: formData.hora_inicio,
        hora_fin: formData.hora_fin,
        profesor: formData.profesor || null
      };
      await api.post('/admin/plantillas/', payload);
      setIsModalOpen(false);
      fetchData();
    } catch (e) {
      toast.error("Error creando plantilla")
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/admin/plantillas/${id}/`);
      fetchPlantillas();
    } catch (e) {
      toast.error("Error eliminando plantilla")
    }
  };

  const promptDelete = (id: string) => {
    setPlantillaToDelete(id);
  };

  if (loading) return <p className="text-muted p-4">Cargando esquema semanal...</p>;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-violett-900">Esquema Semanal</h2>
          <p className="text-sm text-muted">Configura los horarios fijos de clases recurrentes</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>+ Nuevo Horario Fijo</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
        {DIAS.map((dia, index) => {
          const diaNum = index + 1;
          const plantillasDia = plantillas.filter(p => p.dia_semana === diaNum).sort((a,b) => a.hora_inicio.localeCompare(b.hora_inicio));
          
          return (
            <div key={diaNum} className="flex flex-col gap-3">
              <div className="bg-violett-100 text-violett-900 font-bold text-center py-2 rounded-t-xl">
                {dia}
              </div>
              <div className="flex flex-col gap-2">
                {plantillasDia.length === 0 ? (
                  <div className="text-center text-xs text-muted py-4">Sin clases</div>
                ) : (
                  plantillasDia.map(p => (
                    <Card key={p.id} className="text-sm">
                      <CardContent className="p-3">
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-bold">{p.hora_inicio.slice(0,5)}</span>
                          <button onClick={() => promptDelete(p.id)} className="text-red-500 hover:text-red-700 text-xs font-bold">&times;</button>
                        </div>
                        <p className="text-violett-900 font-medium truncate" title={p.clase_nombre}>{p.clase_nombre}</p>
                        {p.profesor ? (
                          <p className="text-xs text-muted truncate mt-1">{p.profesor_nombre} {p.profesor_apellido}</p>
                        ) : (
                          <Badge variant="outline" className="mt-1 text-[10px] bg-yellow-50 text-yellow-700 border-yellow-200">Sin Profesor</Badge>
                        )}
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>    </div>
  );
})}
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Crear Horario Fijo">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">Día de la semana</label>
            <select 
              value={formData.dia_semana}
              onChange={e => setFormData({...formData, dia_semana: e.target.value})}
              className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white"
            >
              {DIAS.map((d, i) => <option key={i+1} value={i+1}>{d}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Hora Inicio</label>
              <input 
                type="time" 
                required 
                value={formData.hora_inicio} 
                onChange={e => setFormData({...formData, hora_inicio: e.target.value})} 
                className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" 
              />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Hora Fin</label>
              <input 
                type="time" 
                required 
                value={formData.hora_fin} 
                onChange={e => setFormData({...formData, hora_fin: e.target.value})} 
                className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" 
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">Clase</label>
            <select 
              required 
              value={formData.clase} 
              onChange={e => setFormData({...formData, clase: e.target.value})} 
              className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white" 
            >
              <option value="">Selecciona una clase</option>
              {clases.map(c => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">Profesor Asignado (Opcional)</label>
            <select 
              value={formData.profesor}
              onChange={e => setFormData({...formData, profesor: e.target.value})}
              className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white"
            >
              <option value="">Dejar libre (Bolsa de trabajo)</option>
              {profesores.map(p => (
                <option key={p.id} value={p.id}>{p.nombre} {p.apellido}</option>
              ))}
            </select>
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-violett-100">
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>Cancelar</Button>
            <Button type="submit">Guardar Horario</Button>
          </div>
        </form>
      </Modal>


                  <ConfirmModal
        isOpen={!!plantillaToDelete}
        onClose={() => setPlantillaToDelete(null)}
        onConfirm={() => {
          if (plantillaToDelete) handleDelete(plantillaToDelete);
        }}
        title="Eliminar Esquema Semanal"
        message="¿Seguro que deseas eliminar este esquema?

Los turnos ya generados seguirán existiendo, pero no se generarán nuevos autómaticamente."
        confirmText="Eliminar"
        isDestructive={true}
      />
    </motion.div>
  );
}
