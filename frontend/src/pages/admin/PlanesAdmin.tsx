import React, { useState, useEffect } from 'react';
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { toast } from "sonner";
import { api } from '../../lib/api';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { motion, AnimatePresence } from 'framer-motion';

export function PlanesAdmin() {
  const [planes, setPlanes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isEditing, setIsEditing] = useState(false);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [nombre, setNombre] = useState('');
  const [cantidadClases, setCantidadClases] = useState(8);
  const [precio, setPrecio] = useState(0);
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
    setIsEditing(true);
    setCurrentId(plan.id);
    setNombre(plan.nombre);
    setCantidadClases(plan.cantidad_clases);
    setPrecio(plan.precio);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setCurrentId(null);
    setNombre('');
    setCantidadClases(8);
    setPrecio(0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isEditing && currentId) {
        await api.put(`/admin/planes/${currentId}/`, {
          nombre, cantidad_clases: cantidadClases, precio, is_active: true
        });
      } else {
        await api.post('/admin/planes/', {
          nombre, cantidad_clases: cantidadClases, precio, is_active: true
        });
      }
      handleCancel();
      fetchPlanes();
    } catch (e) {
      toast.error("Error al guardar el plan")
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/admin/planes/${id}/`);
      fetchPlanes();
    } catch (e) {
      toast.error("Error al eliminar")
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
          <h3 className="font-bold text-lg mb-4 text-foreground">{isEditing ? 'Editar Plan' : 'Crear Nuevo Plan'}</h3>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="col-span-1 md:col-span-2">
              <label className="block text-sm font-semibold mb-1 text-foreground">Nombre</label>
              <input type="text" required value={nombre} onChange={e => setNombre(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Clases</label>
              <input type="number" required min="1" value={cantidadClases} onChange={e => setCantidadClases(Number(e.target.value))} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Precio</label>
              <input type="number" required min="0" step="0.01" value={precio} onChange={e => setPrecio(Number(e.target.value))} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>
            <div className="col-span-1 md:col-span-4 flex justify-end gap-3 mt-2">
              {isEditing && (
                <Button type="button" variant="outline" onClick={handleCancel}>
                  Cancelar
                </Button>
              )}
              <Button type="submit">
                {isEditing ? 'Guardar Cambios' : 'Crear Plan'}
              </Button>
            </div>
          </form>
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
