import React, { useState, useEffect } from 'react';
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { toast } from "sonner";
import { api } from '../../lib/api';
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
      <h2 className="text-3xl font-bold text-violett-900">Paquetes de Clases</h2>

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

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-violett-50/50">
                <tr>
                  <th className="py-4 px-6 text-sm font-bold text-violett-900">Nombre</th>
                  <th className="py-4 px-6 text-sm font-bold text-violett-900 text-center">Clases</th>
                  <th className="py-4 px-6 text-sm font-bold text-violett-900 text-right">Precio</th>
                  <th className="py-4 px-6 text-sm font-bold text-violett-900 text-center">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {planes.map((plan) => (
                    <motion.tr 
                      key={plan.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="border-t border-violett-100 bg-white"
                    >
                      <td className="py-4 px-6 font-medium">{plan.nombre}</td>
                      <td className="py-4 px-6 text-center">{plan.cantidad_clases}</td>
                      <td className="py-4 px-6 text-right font-bold text-violett-700">${plan.precio}</td>
                      <td className="py-4 px-6 text-center space-x-2">
                        <Button size="sm" variant="outline" onClick={() => handleEdit(plan)}>Modificar</Button>
                        <Button size="sm" className="bg-red-500 hover:bg-red-600 text-white" onClick={() => promptDelete(plan.id)}>Borrar</Button>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
            {!loading && planes.length === 0 && (
              <div className="p-8 text-center text-muted">No hay planes registrados.</div>
            )}
          </div>
        </CardContent>
      </Card>
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
