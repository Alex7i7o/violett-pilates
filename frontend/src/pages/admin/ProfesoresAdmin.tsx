import React, { useState, useEffect } from 'react';
import { getAdminProfesores, createAdminProfesor, updateAdminProfesor, deleteAdminProfesor } from '../../lib/adminApi';
import type { Profesor } from '../../lib/adminApi';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { motion, AnimatePresence } from 'framer-motion';

export function ProfesoresAdmin() {
  const [profesores, setProfesores] = useState<Profesor[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [currentId, setCurrentId] = useState<string | null>(null);
  
  const [nombre, setNombre] = useState('');
  const [apellido, setApellido] = useState('');
  const [telefono, setTelefono] = useState('');
  const [email, setEmail] = useState('');
  const [especialidad, setEspecialidad] = useState('');
  const [color, setColor] = useState('#4a306d');

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
    setNombre(''); setApellido(''); setTelefono(''); setEmail(''); setEspecialidad(''); setColor('#4a306d');
    setShowModal(true);
  };

  const openEditModal = (prof: Profesor) => {
    setIsEditing(true);
    setCurrentId(prof.id);
    setNombre(prof.nombre); setApellido(prof.apellido); setTelefono(prof.telefono || '');
    setEmail(prof.email || ''); setEspecialidad(prof.especialidad || ''); setColor(prof.color_identificador || '#4a306d');
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('¿Seguro que deseas eliminar este profesor?')) return;
    try {
      await deleteAdminProfesor(id);
      fetchProfesores();
    } catch (e) {
      alert("Error eliminando profesor");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const data = { nombre, apellido, telefono, email, especialidad, color_identificador: color };
    try {
      if (isEditing && currentId) await updateAdminProfesor(currentId, data);
      else await createAdminProfesor(data);
      setShowModal(false);
      fetchProfesores();
    } catch (err) {
      alert("Error guardando");
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
                        <div className="text-sm text-foreground">{prof.telefono || 'Sin teléfono'}</div>
                        <div className="text-sm text-muted">{prof.email || 'Sin email'}</div>
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
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Nombre</label>
              <input type="text" required value={nombre} onChange={e=>setNombre(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Apellido</label>
              <input type="text" required value={apellido} onChange={e=>setApellido(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">Email</label>
            <input type="email" value={email} onChange={e=>setEmail(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">Teléfono</label>
            <input type="text" value={telefono} onChange={e=>setTelefono(e.target.value)} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Especialidad</label>
              <input type="text" value={especialidad} onChange={e=>setEspecialidad(e.target.value)} placeholder="Ej. Pilates" className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1 text-foreground">Color</label>
              <input type="color" value={color} onChange={e=>setColor(e.target.value)} className="w-full h-11 px-1 py-1 rounded-xl cursor-pointer border border-violett-200" />
            </div>
          </div>
          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-violett-100">
            <Button type="button" variant="outline" onClick={() => setShowModal(false)}>Cancelar</Button>
            <Button type="submit">Guardar</Button>
          </div>
        </form>
      </Modal>
    </motion.div>
  );
}
