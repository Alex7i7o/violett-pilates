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
  const [editId, setEditId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [currentId, setCurrentId] = useState<string | null>(null);
  
    const [apellido, setApellido] = useState('');
    const [profesorToDelete, setProfesorToDelete] = useState<string | null>(null);
    const [especialidad, setEspecialidad] = useState('');
  const [color, setColor] = useState('#4a306d');
  const [fechaNacimiento, setFechaNacimiento] = useState('');
  const [sexo, setSexo] = useState('');

  const fetchProfesores = async () => {
    try {
      setLoading(true);
      const res = await getAdminProfesores();
      setProfesores(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfesores();
  }, []);

  const openNewModal = () => {
    setIsEditing(false);
    setCurrentId(null);
    setNombre(''); setApellido(''); setTelefono(''); setEmail(''); setEspecialidad(''); setColor('#4a306d'); setFechaNacimiento(''); setSexo('');
    setShowModal(true);
  };

  const openEditModal = (prof: Profesor) => {
    setIsEditing(true);
    setCurrentId(prof.id);
    setNombre(prof.nombre); setApellido(prof.apellido); setTelefono(prof.telefono || '');
    setEmail(prof.email || ''); setEspecialidad(prof.especialidad || ''); setColor(prof.color_identificador || '#4a306d'); setFechaNacimiento(prof.fecha_nacimiento || ''); setSexo(prof.sexo || '');
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteAdminProfesor(id);
      fetchData();
    } catch (e) {
      toast.error("Error eliminando profesor")
    }
  };

  const promptDelete = (id: string) => {
    setProfesorToDelete(id);
  };

    const handleSubmit = async (data: ProfesorFormData) => {
    try {
      if (editId) {
        await api.put(`/admin/profesores/${editId}/`, data);
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

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={isEditing ? 'Modificar Profesor' : 'Nuevo Profesor'}>
        {editId ? (
          <ProfesorForm 
            initialData={{ nombre: profesores.find(p => p.id === editId)?.nombre || '', email: profesores.find(p => p.id === editId)?.email || '', telefono: profesores.find(p => p.id === editId)?.telefono || '', color: profesores.find(p => p.id === editId)?.color || '#6d28d9' }} 
            onSubmit={handleSubmit} 
            onCancel={() => setShowModal(false)} 
            isSubmitting={false} 
            submitLabel="Actualizar Profesor" 
          />
        ) : (
          <ProfesorForm 
            onSubmit={handleSubmit} 
            onCancel={() => setShowModal(false)} 
            isSubmitting={false} 
            submitLabel="Crear Profesor" 
          />
        )}
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

