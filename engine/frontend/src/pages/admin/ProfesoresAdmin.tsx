import React, { useState, useEffect } from 'react';
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { InputField } from '../../components/ui/InputField';
import { SelectField } from '../../components/ui/SelectField';
import { toast } from "sonner";
import { getAdminProfesores, createAdminProfesor, updateAdminProfesor, deleteAdminProfesor } from '../../lib/adminApi';
import type { Profesor } from '../../lib/adminApi';
import { Skeleton } from '../../components/ui/Skeleton';
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
      const res = await getAdminProfesores();
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
      await deleteAdminProfesor(id);
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
        await updateAdminProfesor(currentProfesor.id, data);
        toast.success('Profesor actualizado');
      } else {
        await createAdminProfesor(data);
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
        <h2 className="text-3xl font-bold text-primary-main">Staff y Profesores</h2>
        <Button onClick={openNewModal}>+ Nuevo Profesor</Button>
      </div>

            {!loading && profesores.length === 0 && (
        <div className="p-8 text-center text-muted">No hay profesores registrados.</div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <AnimatePresence>
          {profesores.map(prof => (
            <motion.div
              key={prof.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              layout
            >
              <Card className="hover:shadow-md transition-shadow h-full flex flex-col">
                <CardContent className="p-6 flex flex-col h-full">
                  <div className="flex items-start gap-4 mb-4">
                    <div className="h-12 w-12 rounded-full flex items-center justify-center text-white font-bold text-lg shrink-0 shadow-sm" style={{ backgroundColor: prof.color_identificador }}>
                      {prof.nombre.charAt(0)}{prof.apellido.charAt(0)}
                    </div>
                    <div>
                      <h3 className="font-bold text-foreground text-lg leading-tight">{prof.nombre} {prof.apellido}</h3>
                      <span className="inline-block mt-1 px-2.5 py-0.5 text-xs font-semibold rounded-full bg-primary-light text-primary-main">
                        {prof.especialidad || 'General'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-2 mb-6 flex-1 text-sm">
                    <div className="flex items-center text-muted">
                      <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                      {prof.telefono || 'Sin teléfono'}
                    </div>
                    <div className="flex items-center text-muted break-all">
                      <svg className="w-4 h-4 mr-2 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                      {prof.email || 'Sin email'}
                    </div>
                  </div>
                  
                  <div className="flex justify-end gap-2 mt-auto pt-4 border-t border-primary-light/50">
                    <Button size="sm" variant="outline" onClick={() => openEditModal(prof)}>Editar</Button>
                    <Button size="sm" variant="outline" className="text-red-500 hover:bg-red-50 hover:text-red-600 border-red-100" onClick={() => setProfesorToDelete(prof.id)}>Eliminar</Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

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

