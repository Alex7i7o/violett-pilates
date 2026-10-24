import React, { useState, useEffect } from 'react';
import { ConfirmModal } from "../../components/ui/ConfirmModal";
import { InputField } from '../../components/ui/InputField';
import { SelectField } from '../../components/ui/SelectField';
import { toast } from "sonner";
import { getAdminProfesores, createAdminProfesor, updateAdminProfesor, deleteAdminProfesor, reenviarAccesoProfesor } from '../../lib/adminApi';
import type { Profesor } from '../../lib/adminApi';
import { Skeleton } from '../../components/ui/Skeleton';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { ProfesorForm, type ProfesorFormData } from '../../components/admin/ProfesorForm';
import { Modal } from '../../components/ui/Modal';
import { motion, AnimatePresence } from 'framer-motion';
import { KeyRound, Calendar, ChevronDown, ChevronUp } from 'lucide-react';

export function ProfesoresAdmin() {
  const [profesores, setProfesores] = useState<Profesor[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [showModal, setShowModal] = useState(false);
  const [currentProfesor, setCurrentProfesor] = useState<Profesor | null>(null);
  const [profesorToDelete, setProfesorToDelete] = useState<string | null>(null);
  const [sendingEmailId, setSendingEmailId] = useState<string | null>(null);
  const [expandedProfesorIds, setExpandedProfesorIds] = useState<Record<string, boolean>>({});

  const toggleExpandProfesor = (id: string) => {
    setExpandedProfesorIds(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handleReenviarAcceso = async (prof: Profesor) => {
    if (!prof.email) {
      toast.error('Este profesor no tiene un email configurado.');
      return;
    }
    setSendingEmailId(prof.id);
    try {
      const res = await reenviarAccesoProfesor(prof.id);
      toast.success(res.data?.detail || `Correo enviado exitosamente a ${prof.email}`);
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Error al enviar el correo';
      toast.error(msg, { duration: 6000 });
    } finally {
      setSendingEmailId(null);
    }
  };

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
                  
                  <div className="space-y-2 mb-4 text-sm">
                    <div className="flex items-center text-muted">
                      <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                      {prof.telefono || 'Sin teléfono'}
                    </div>
                    <div className="flex items-center text-muted break-all">
                      <svg className="w-4 h-4 mr-2 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                      {prof.email || 'Sin email'}
                    </div>
                  </div>

                  {/* Horarios / Clases Fijas (Badge + Toggle) */}
                  <div className="mt-auto mb-4 pt-3 border-t border-slate-100">
                    {(() => {
                      const clases = prof.clases_fijas || [];
                      const isExpanded = !!expandedProfesorIds[prof.id];
                      const diasUnicos = Array.from(new Set(clases.map(c => c.dia_nombre.slice(0, 3))));
                      const diasResumen = diasUnicos.join(', ');

                      if (clases.length === 0) {
                        return (
                          <div className="px-3 py-2 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs text-muted">
                            <span className="flex items-center gap-1.5 font-medium text-slate-500">
                              <Calendar className="w-3.5 h-3.5 text-slate-400" />
                              Sin clases fijas asignadas
                            </span>
                            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">0 turnos</span>
                          </div>
                        );
                      }

                      return (
                        <div className="space-y-1.5">
                          <button
                            type="button"
                            onClick={() => toggleExpandProfesor(prof.id)}
                            className={`w-full flex items-center justify-between px-3 py-2 rounded-xl border text-xs font-semibold transition-all duration-200 ${
                              isExpanded 
                                ? 'bg-primary-light text-primary-main border-primary-light shadow-2xs' 
                                : 'bg-primary-light/40 text-primary-main border-primary-light/60 hover:bg-primary-light/70'
                            }`}
                          >
                            <div className="flex items-center gap-2 truncate">
                              <Calendar className="w-3.5 h-3.5 shrink-0 text-primary-main" />
                              <span className="truncate">
                                <span className="font-bold">{diasResumen}</span>
                                <span className="text-primary-main/70 font-normal"> · {clases.length} {clases.length === 1 ? 'clase fija' : 'clases fijas'}</span>
                              </span>
                            </div>
                            <div className="flex items-center gap-1 shrink-0 ml-2">
                              <span className="text-[11px] font-medium text-primary-main/80">
                                {isExpanded ? 'Ocultar' : 'Ver horarios'}
                              </span>
                              {isExpanded ? (
                                <ChevronUp className="w-3.5 h-3.5 text-primary-main" />
                              ) : (
                                <ChevronDown className="w-3.5 h-3.5 text-primary-main" />
                              )}
                            </div>
                          </button>

                          <AnimatePresence>
                            {isExpanded && (
                              <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.2 }}
                                className="overflow-hidden"
                              >
                                <div className="pt-1.5 space-y-1.5 max-h-48 overflow-y-auto pr-1">
                                  {clases.map((cf) => (
                                    <div
                                      key={cf.id}
                                      className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-slate-50/90 border border-slate-200/70 text-xs"
                                    >
                                      <div className="flex items-center gap-2">
                                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary-main text-white shadow-2xs">
                                          {cf.dia_nombre.slice(0, 3)}
                                        </span>
                                        <span className="font-semibold text-slate-700">
                                          {cf.hora_inicio} a {cf.hora_fin} hs
                                        </span>
                                      </div>
                                      <span className="text-[11px] text-primary-main font-medium truncate ml-2">
                                        {cf.clase_nombre}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      );
                    })()}
                  </div>
                  
                  <div className="flex flex-wrap items-center justify-between gap-2 mt-auto pt-4 border-t border-primary-light/50">
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => handleReenviarAcceso(prof)}
                      disabled={sendingEmailId === prof.id || !prof.email}
                      className="text-xs text-primary-main hover:bg-primary-light/40 border-primary-light flex items-center gap-1.5 font-semibold"
                      title={prof.email ? `Reenviar correo para definir contraseña a ${prof.email}` : 'Sin email'}
                    >
                      <KeyRound className={`w-3.5 h-3.5 ${sendingEmailId === prof.id ? 'animate-spin' : ''}`} />
                      <span>{sendingEmailId === prof.id ? 'Enviando...' : 'Reenviar Contraseña'}</span>
                    </Button>

                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline" onClick={() => openEditModal(prof)}>Editar</Button>
                      <Button size="sm" variant="outline" className="text-red-500 hover:bg-red-50 hover:text-red-600 border-red-100" onClick={() => setProfesorToDelete(prof.id)}>Eliminar</Button>
                    </div>
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

