import React, { useState, useEffect } from 'react';
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { toast } from "sonner";
import { api } from '../../lib/api';
import { Skeleton } from '../../components/ui/Skeleton';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { motion, AnimatePresence } from 'framer-motion';
import { ClaseForm, type ClaseFormData } from '../../components/admin/ClaseForm';

export function ClasesAdmin() {
  const [clases, setClases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [claseToDelete, setClaseToDelete] = useState<string | null>(null);

  const fetchClases = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/clases/');
      setClases(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Error al cargar disciplinas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClases();
  }, []);

  const handleEdit = (clase: any) => {
    setCurrentId(clase.id);
  };

  const handleCancel = () => {
    setCurrentId(null);
  }

  const handleSubmit = async (data: ClaseFormData) => {
    try {
      if (currentId) {
        await api.put(`/admin/clases/${currentId}/`, data);
        toast.success('Disciplina actualizada');
      } else {
        await api.post('/admin/clases/', data);
        toast.success('Disciplina creada');
      }
      setCurrentId(null);
      fetchClases();
    } catch (e) {
      console.error(e);
      toast.error('Error al guardar disciplina');
    }
  };

  const handleDelete = async () => {
    if (!claseToDelete) return;
    try {
      await api.delete(`/admin/clases/${claseToDelete}/`);
      toast.success('Disciplina eliminada');
      fetchClases();
    } catch (e) {
      console.error(e);
      toast.error('Error al eliminar disciplina');
    } finally {
      setClaseToDelete(null);
    }
  };

  const currentClase = currentId ? clases.find(c => c.id === currentId) : null;
  
  // Convert backend data to formdata for initialData
  const initialData: ClaseFormData | null = currentClase ? {
      nombre: currentClase.nombre,
      descripcion: currentClase.descripcion || '',
      duracion_minutos: currentClase.duracion_minutos,
      cupo_maximo: currentClase.cupo_maximo,
      cupo_minimo: currentClase.cupo_minimo
  } : null;

  if (loading && clases.length === 0) {
    return <div className="p-8">Cargando disciplinas...</div>;
  }

  return (
    <div className="p-4 md:p-8 max-w-4xl mx-auto space-y-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-violett-900">Disciplinas</h1>
      </div>

      <Card className="shadow-sm border-violett-100">
        <CardContent className="p-6">
          <h2 className="text-xl font-bold text-foreground mb-4">
            {currentId ? 'Editar Disciplina' : 'Nueva Disciplina'}
          </h2>
          <ClaseForm 
            initialData={initialData} 
            isEditing={!!currentId} 
            onSubmit={handleSubmit} 
            onCancel={handleCancel} 
          />
        </CardContent>
      </Card>

      <div className="space-y-4 relative min-h-[200px]">
        <h2 className="text-xl font-bold text-foreground mb-4">Disciplinas Activas</h2>
        {clases.length === 0 ? (
          <p className="text-muted">No hay disciplinas registradas.</p>
        ) : (
          <AnimatePresence mode="popLayout">
            {clases.map(clase => (
              <motion.div
                layout
                key={clase.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <Card className="hover:shadow-md transition-shadow border-violett-100/50">
                  <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-bold text-violett-900">{clase.nombre}</h3>
                      <p className="text-sm text-muted">{clase.duracion_minutos} min | Cupo: {clase.cupo_minimo}-{clase.cupo_maximo} alumnos</p>
                      {clase.descripcion && <p className="text-sm text-muted mt-1 italic">{clase.descripcion}</p>}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleEdit(clase)}>
                        Editar
                      </Button>
                      <Button variant="destructive" size="sm" onClick={() => setClaseToDelete(clase.id)}>
                        Eliminar
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      <ConfirmModal
        isOpen={!!claseToDelete}
        onClose={() => setClaseToDelete(null)}
        onConfirm={handleDelete}
        title="Eliminar Disciplina"
        message="¿Estás seguro de que deseas eliminar esta disciplina? No se podrán crear nuevas clases de este tipo."
        confirmText="Sí, eliminar"
        isDestructive={true}
      />
    </div>
  );
}
