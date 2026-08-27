import React, { useState, useEffect } from 'react';
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { InputField } from '../../components/ui/InputField';
import { SelectField } from '../../components/ui/SelectField';
import { toast } from "sonner";
import { getAdminProfesores, createAdminProfesor, updateAdminProfesor, deleteAdminProfesor } from '../../lib/adminApi';
import type { Profesor } from '../../lib/adminApi';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { ProfesorForm, type ProfesorFormData } from '../../components/admin/ProfesorForm';
import { Modal } from '../../components/ui/Modal';
import { motion, AnimatePresence } from 'framer-motion';

export function ProfesoresAdmin() {
  const [profesores, setProfesores] = useState<Profesor[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [currentProfesor, setCurrentProfesor] = useState<Profesor | null>(null);
  const [profesorToDelete, setProfesorToDelete] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const res = await api.get('/admin/profesores/');
      setProfesores(res.data);
      setLoading(false);
    } catch (e) {
      toast.error('Error al cargar profesores');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openNewModal = () => {
    setCurrentProfesor(null);
    setShowModal(true);
  };

  const openEditModal = (prof: Profesor) => {
    setCurrentProfesor(prof);
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/admin/profesores/${id}/`);
      toast.success('Profesor eliminado');
      fetchData();
    } catch (e) {
      toast.error('Error al eliminar profesor');
    } finally {
      setProfesorToDelete(null);
    }
  };

  const handleSubmit = async (data: any) => {
    try {
      if (currentProfesor) {
        await api.put(`/admin/profesores/${currentProfesor.id}/`, data);
        toast.success('Profesor actualizado');
      } else {
        await api.post('/admin/profesores/', data);
        toast.success('Profesor creado');
      }
      setShowModal(false);
      fetchData();
    } catch (e) {
      console.error(e);
      toast.error('Error al guardar el profesor');
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-violett-900">Staff y Profesores</h2>
        <Button onClick={openNewModal}>+ Nuevo Profesor</Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-violett-50/50">
                <tr>
                  <th className="py-4 px-6 text-sm font-bold text-violett-900">Profesor</th>
                  <th className="py-4 px-6 text-sm font-bold text-violett-900">Contacto</th>
                  <th className="py-4 px-6 text-sm font-bold text-violett-900">Especialidad</th>
                  <th className="py-4 px-6 text-sm font-bold text-violett-900 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {profesores.map((prof) => (
                    <motion.tr 
                      key={prof.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="border-t border-violett-100 bg-white"
                    >
                      <td className="py-4 px-6 align-middle">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-full flex items-center justify-center text-white font-bold" style={{ backgroundColor: prof.color_identificador }}>
                            {prof.nombre.charAt(0)}{prof.apellido.charAt(0)}
                          </div>
                          <div className="font-bold text-foreground">{prof.nombre} {prof.apellido}</div>
                        </div>
                      </td>
                      <td className="py-4 px-6 align-middle">
                        <div className="text-sm text-foreground">Tel: {prof.telefono || 'Sin teléfono'}</div>
                        <div className="text-sm text-muted">{prof.email || 'Sin email'}</div>
                        <div className="text-xs font-medium text-violett-600 mt-1">Edad: {prof.edad !== null ? `${prof.edad} años` : '-'} | Sexo: {prof.sexo || '-'}</div>
                      </td>
                      <td className="py-4 px-6 align-middle">
                        <span className="px-3 py-1 text-xs font-semibold rounded bg-violett-100 text-violett-900 border border-violett-200">
                          {prof.especialidad || 'General'}
                        </span>
                      </td>
                      <td className="py-4 px-6 align-middle text-right space-x-2">
                        <Button size="sm" variant="outline" onClick={() => openEditModal(prof)}>Modificar</Button>
                        <Button size="sm" className="bg-red-500 hover:bg-red-600 text-white" onClick={() => handleDelete(prof.id)}>Borrar</Button>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
            {!loading && profesores.length === 0 && (
              <div className="p-8 text-center text-muted">No hay profesores registrados.</div>
            )}
          </div>
        </CardContent>
      </Card>

            <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={currentProfesor ? 'Modificar Profesor' : 'Nuevo Profesor'}>
        <ProfesorForm 
          initialData={currentProfesor ? { nombre: currentProfesor.nombre, apellido: currentProfesor.apellido, email: currentProfesor.email || '', telefono: currentProfesor.telefono || '', color_identificador: currentProfesor.color_identificador || '#6d28d9' } : undefined} 
          onSubmit={handleSubmit} 
          onCancel={() => setShowModal(false)} 
          isSubmitting={false} 
          submitLabel={currentProfesor ? "Actualizar Profesor" : "Crear Profesor"}
        />
      </Modal>
      <ConfirmModal
        isOpen={!!profesorToDelete}
        onClose={() => setProfesorToDelete(null)}
        onConfirm={() => {
          if (profesorToDelete) handleDelete(profesorToDelete);
        }}
        title="Eliminar Profesor"
        message="Seguro que deseas eliminar este profesor? Se reasignarán sus clases."
        confirmText="Eliminar"
        isDestructive={true}
      />
    </motion.div>
  );
}

