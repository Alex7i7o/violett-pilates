import React, { useState, useEffect } from 'react';
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { toast } from "sonner";
import { api } from '../../lib/api';
import { Skeleton } from '../../components/ui/Skeleton';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { motion, AnimatePresence } from 'framer-motion';
import { PlanForm, type PlanFormData } from '../../components/admin/PlanForm';

export function PlanesAdmin() {
  const [planes, setPlanes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [planToDelete, setPlanToDelete] = useState<string | null>(null);

  const fetchPlanes = async () => {
    try {
      setLoading(true);
      const res = await api.get('/admin/planes/');
      setPlanes(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlanes();
  }, []);

  const handleEdit = (plan: any) => {
    setCurrentId(plan.id);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCancel = () => {
    setCurrentId(null);
  }

  const handleSubmit = async (data: PlanFormData) => {
    try {
      if (currentId) {
        await api.put(`/admin/planes/${currentId}/`, {
          nombre: data.nombre,
          cantidad_clases: data.clases_por_mes,
          precio: data.precio
        });
        toast.success('Plan actualizado');
      } else {
        await api.post('/admin/planes/', {
          nombre: data.nombre,
          cantidad_clases: data.clases_por_mes,
          precio: data.precio
        });
        toast.success('Plan creado');
      }
      handleCancel();
      fetchPlanes();
    } catch (e) {
      console.error(e);
      toast.error('Error al guardar el plan');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/admin/planes/${id}/`);
      toast.success("Plan eliminado");
      fetchPlanes();
    } catch (e) {
      toast.error("Error al eliminar");
    } finally {
      setPlanToDelete(null);
    }
  };

  const promptDelete = (id: string) => {
    setPlanToDelete(id);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <h2 className="text-3xl font-bold text-primary-main">Paquetes de Clases</h2>

      <Card>
        <CardContent className="pt-6">
          <h3 className="font-bold text-lg mb-4 text-foreground">{currentId ? 'Editar Plan' : 'Crear Nuevo Plan'}</h3>
          <PlanForm 
            initialData={currentId ? { 
              nombre: planes.find(p => p.id === currentId)?.nombre || '', 
              clases_por_mes: planes.find(p => p.id === currentId)?.cantidad_clases || 0, 
              precio: planes.find(p => p.id === currentId)?.precio || 0 
            } : null} 
            onSubmit={handleSubmit} 
            onCancel={handleCancel} 
            isEditing={!!currentId} 
          />
        </CardContent>
      </Card>

            {!loading && planes.length === 0 && (
        <div className="p-8 text-center text-muted">No hay planes registrados.</div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <AnimatePresence>
          {planes.map(plan => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              layout
            >
              <Card className="hover:shadow-md transition-shadow h-full flex flex-col">
                <CardContent className="p-6 flex flex-col h-full">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-bold text-foreground text-xl leading-tight text-primary-hover mb-1">
                        {plan.nombre}
                      </h3>
                      <span className="inline-flex items-center text-sm font-semibold text-muted bg-primary-light/50 px-3 py-1 rounded-full">
                        <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        {plan.cantidad_clases} clases
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-black text-primary-main">
                        
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex justify-end gap-2 mt-auto pt-6 border-t border-primary-light/50">
                    <Button size="sm" variant="outline" onClick={() => handleEdit(plan)}>Editar</Button>
                    <Button size="sm" variant="outline" className="text-red-500 hover:bg-red-50 hover:text-red-600 border-red-100" onClick={() => promptDelete(plan.id)}>Eliminar</Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      <ConfirmModal
        isOpen={!!planToDelete}
        onClose={() => setPlanToDelete(null)}
        onConfirm={() => {
          if (planToDelete) handleDelete(planToDelete);
        }}
        title="Eliminar Plan"
        message="Seguro que deseas eliminar este plan?"
        confirmText="Eliminar"
        isDestructive={true}
      />
    </motion.div>
  );
}

