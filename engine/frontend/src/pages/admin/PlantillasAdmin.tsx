import React, { useState, useEffect } from 'react';
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { toast } from "sonner";
import { api } from '../../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { PlantillaForm } from '../../components/admin/PlantillaForm';
import { motion, AnimatePresence } from 'framer-motion';

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

export function PlantillasAdmin() {
  const [plantillas, setPlantillas] = useState<any[]>([]);
  const [clases, setClases] = useState<any[]>([]);
  const [profesores, setProfesores] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [plantillaToDelete, setPlantillaToDelete] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<number>(0);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const handleEdit = (id: string) => {
    setEditId(id);
    setIsModalOpen(true);
  };
  const handleCreateClick = () => {
    setEditId(null);
    setIsModalOpen(true);
  };

  
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

    const handleCreate = async (data: any) => {
    try {
      const payload = { ...data };
      if (!payload.profesor) payload.profesor = null;
      
      if (editId) {
        await api.put(`/admin/plantillas/${editId}/`, payload);
        toast.success('Horario actualizado');
      } else {
        await api.post('/admin/plantillas/', payload);
        toast.success('Horario creado eééxitosamente');
      }
      setIsModalOpen(false);
      fetchData();
    } catch (e) {
      console.error(e);
      toast.error('Error al guardar el horario');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/admin/plantillas/${id}/`);
      fetchData();
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
      <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4 mb-2">
        <div>
          <h1 className="text-2xl font-bold mb-1">Esquema Semanal</h1>
          <p className="text-sm text-muted">Este es el esqueleto de tu negocio. Las clases que agregues aquí se generarán automáticamente todas las semanas en la Agenda.</p>
        </div>
        <Button className="w-full md:w-auto shrink-0" onClick={handleCreateClick}>+ Nuevo Horario Fijo</Button>
      </div>

      {/* Mobile Tabs */}
        <div className="md:hidden flex overflow-x-auto gap-2 pb-2 mb-2 hide-scrollbar" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
          {DIAS.map((dia, idx) => (
            <button 
              key={idx}
              onClick={() => setSelectedDay(idx)}
              className={`px-5 py-2.5 rounded-2xl whitespace-nowrap font-bold text-sm transition-all flex-shrink-0 ${selectedDay === idx ? 'bg-primary-main text-white shadow-md' : 'bg-primary-light/40 text-primary-main hover:bg-primary-light/60'}`}
            >
              {dia}
            </button>
          ))}
        </div>
  
        {/* Days container */}
        <div className="flex flex-col md:grid md:grid-cols-7 gap-4 pb-4">
          {DIAS.map((dia, index) => {
            const diaNum = index + 1;
            const isSelected = selectedDay === index;
            const plantillasDia = plantillas.filter(p => p.dia_semana === diaNum).sort((a,b) => a.hora_inicio.localeCompare(b.hora_inicio));
            
            return (
              <div key={diaNum} className={`${isSelected ? 'flex' : 'hidden'} md:flex flex-col gap-3`}>
                <div className="hidden md:block bg-primary-light/50 text-primary-main font-bold text-center py-2 rounded-xl mb-1">
                  {dia}
                </div>
                
                <div className="flex flex-col gap-2">
                  {plantillasDia.length === 0 ? (
                    <div className="text-center text-xs text-muted py-8 md:py-4 bg-slate-50 rounded-xl border border-dashed border-slate-200">Sin clases</div>
                  ) : (
                    plantillasDia.map(p => (
                      <Card key={p.id} className="text-sm cursor-pointer border-primary-light/50 hover:border-primary-main transition-all hover:shadow-md hover:-translate-y-0.5" onClick={() => handleEdit(p.id)}>
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-bold text-lg text-foreground leading-none">{p.hora_inicio.slice(0,5)}</span>
                            <button onClick={(e) => { e.stopPropagation(); promptDelete(p.id); }} className="text-red-400 hover:text-red-600 hover:bg-red-50 h-6 w-6 rounded-full flex items-center justify-center transition-colors">&times;</button>
                          </div>
                          <p className="text-primary-main font-bold truncate" title={p.clase_nombre}>{p.clase_nombre}</p>
                          {p.profesor ? (
                            <p className="text-xs text-muted truncate mt-1 font-medium">{p.profesor_nombre} {p.profesor_apellido}</p>
                          ) : (
                            <Badge variant="outline" className="mt-1.5 text-[10px] uppercase font-bold bg-yellow-50 text-yellow-700 border-yellow-200">Sin Profesor</Badge>
                          )}
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editId ? "Modificar Horario Fijo" : "Crear Horario Fijo"}>
        {editId ? (
          <PlantillaForm 
            initialData={{ 
              dia_semana: plantillas.find(p => p.id === editId)?.dia_semana.toString() || '1', 
              hora_inicio: plantillas.find(p => p.id === editId)?.hora_inicio || '09:00', 
              hora_fin: plantillas.find(p => p.id === editId)?.hora_fin || '10:00', 
              clase: plantillas.find(p => p.id === editId)?.clase || '', 
              profesor: plantillas.find(p => p.id === editId)?.profesor || '' 
            }}
            profesores={profesores}
            clases={clases}
            onSubmit={handleCreate} 
            onCancel={() => setIsModalOpen(false)} 
            isSubmitting={false} 
          />
        ) : (
          <PlantillaForm 
            profesores={profesores}
            clases={clases}
            onSubmit={handleCreate} 
            onCancel={() => setIsModalOpen(false)} 
            isSubmitting={false} 
          />
        )}
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

