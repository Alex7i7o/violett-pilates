import React, { useState, useEffect } from 'react';
import { toast } from "sonner";
import { useClientConfig } from '../../context/ClientConfigContext';
import { getAdminAlumnos, createAdminAlumno, updateAdminAlumno, asignarPlanAlumno } from '../../lib/adminApi';
import type { UsuarioAdmin } from '../../lib/adminApi';
import { api } from '../../lib/api';
import { Skeleton } from '../../components/ui/Skeleton';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { AlumnoForm, type AlumnoFormData } from '../../components/admin/AlumnoForm';
import { Modal } from '../../components/ui/Modal';
import { ConfirmModal } from '../../components/ui/ConfirmModal';
import { Badge } from '../../components/ui/Badge';
import { InputField } from '../../components/ui/InputField';
import { SelectField } from '../../components/ui/SelectField';
import { motion, AnimatePresence } from 'framer-motion';
import { EditStudentModal } from './components/EditStudentModal';

export function AlumnosAdmin() {
  const config = useClientConfig();
  const isEstÃ©tica = config.client_id === 'violett_estetica';
  const labelPlural = isEstÃ©tica ? 'pacientes' : 'alumnas';
  const labelSingular = isEstÃ©tica ? 'paciente' : 'alumna';
  const LabelPluralTitle = isEstÃ©tica ? 'Pacientes' : 'Alumnas';
  const [alumnos, setAlumnos] = useState<UsuarioAdmin[]>([]);
  const [search, setSearch] = useState('');
  const [minAge, setMinAge] = useState('');
  const [maxAge, setMaxAge] = useState('');
  const [estadoFilter, setEstadoFilter] = useState('Todos');
  const [showFilters, setShowFilters] = useState(false);
  const [sexoFilter, setSexoFilter] = useState('Todos');
  const [loading, setLoading] = useState(true);
  const [showNewModal, setShowNewModal] = useState(false);
  const [creating, setCreating] = useState(false);
  
  const [selectedAlumno, setSelectedAlumno] = useState<any>(null);
  const [alumnoToDelete, setAlumnoToDelete] = useState<string | null>(null);
  
  const [planes, setPlanes] = useState<any[]>([]);
  
  useEffect(() => {
    fetchAlumnos();
    fetchPlanes();
  }, []);

  const fetchPlanes = async () => {
    try {
      const res = await api.get('/admin/planes/');
      setPlanes(res.data);
    } catch (e) {
      console.error(e);
    }
  }

  const fetchAlumnos = async () => {
    try {
      const res = await getAdminAlumnos();
      setAlumnos(res.data);
    } catch (error) {
      toast.error(`Error al cargar `);
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteAlumno = async (id: string) => {
    try {
      await api.delete(`/admin/alumnos/${id}/`);
      toast.success(` eliminada eÃ©Ã©xitosamente`);
      setAlumnos(alumnos.filter(a => a.id !== id));
      if (selectedAlumno?.id === id) setSelectedAlumno(null);
    } catch (error) {
      toast.error(`Error al eliminar `);
    }
  };

  const handleCreateAlumno = async (data: AlumnoFormData) => {
    setCreating(true);
    try {
      await api.post('/admin/alumnos/', data);
      toast.success(` creada eÃ©Ã©xitosamente`);
      fetchAlumnos();
      setShowNewModal(false);
    } catch (e: any) {
      console.error(e);
      toast.error('`Error al crear . ` ' + (e.response?.data?.detail || ''));
    } finally {
      setCreating(false);
    }
  };

  const filteredAlumnos = alumnos.filter(a => {
    const s = search.toLowerCase();
    if (search && !a.nombre.toLowerCase().includes(s) && !a.apellido.toLowerCase().includes(s) && !(a.telefono || '').includes(s)) return false;
    if (minAge && (a.edad === null || a.edad < parseInt(minAge))) return false;
    if (maxAge && (a.edad === null || a.edad > parseInt(maxAge))) return false;
    if (sexoFilter !== 'Todos' && a.sexo !== sexoFilter) return false;
    if (estadoFilter !== 'Todos') {
      const estado = a.plan_activo?.estado || 'Sin plan';
      let estadoCalculado = 'Sin plan';
      if (estado === 'ACTIVO') estadoCalculado = 'Activo';
      else if (estado === 'AGOTADO') estadoCalculado = 'Pendiente';
      if (estadoFilter !== estadoCalculado) return false;
    }
    return true;
  });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h2 className="text-3xl font-bold text-primary-main">Directorio de {LabelPluralTitle}</h2>
        <Button onClick={() => setShowNewModal(true)}>{`+ Nuevo ${labelSingular}`}</Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Card key={i}><CardContent className="pt-6"><Skeleton className="h-24 w-full" /></CardContent></Card>
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          <Card className="mb-6">
            <CardContent className="pt-6">
              <div className="flex gap-4 items-center">
                <div className="relative flex-1 max-w-2xl">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="w-5 h-5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                  </div>
                  <input 
                    type="text"
                    placeholder="Buscar por nombre, apellido o telÃ©fono..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main shadow-sm"
                  />
                </div>
                <Button 
                  variant={showFilters ? 'primary' : 'outline'} 
                  onClick={() => setShowFilters(!showFilters)}
                  className="shrink-0 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
                  Filtros
                </Button>
              </div>
              
              <AnimatePresence>
                {showFilters && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="pt-4 mt-4 border-t border-primary-light grid grid-cols-2 md:grid-cols-4 gap-4">
                      <SelectField label="Estado" name="estado" value={estadoFilter} onChange={e => setEstadoFilter(e.target.value)} options={[{value:'Todos',label:'Todos'},{value:'Activo',label:'Activo'},{value:'Pendiente',label:'Pendiente'},{value:'Sin plan',label:'Sin plan'}]} />
                      <SelectField label="Sexo" name="sexo" value={sexoFilter} onChange={e => setSexoFilter(e.target.value)} options={[{value:'Todos',label:'Todos'},{value:'Femenino',label:'Femenino'},{value:'Masculino',label:'Masculino'},{value:'Otro',label:'Otro'}]} />
                      <InputField label="Edad MÃ­nima" name="minAge" type="number" value={minAge} onChange={e => setMinAge(e.target.value)} />
                      <InputField label="Edad MÃ¡xima" name="maxAge" type="number" value={maxAge} onChange={e => setMaxAge(e.target.value)} />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence>
              {filteredAlumnos.map(alumno => (
                <motion.div 
                  key={alumno.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.2 }}
                >
                  <Card 
                    className="h-full flex flex-col justify-between hover:shadow-glow transition-shadow cursor-pointer" 
                    onClick={() => setSelectedAlumno(alumno)}
                  >
                    <CardContent className="pt-6">
                      <h3 className="text-xl font-bold text-foreground">{alumno.nombre || 'Sin Nombre'} {alumno.apellido || ''}</h3>
                      <p className="text-sm text-muted mt-1">
                        Email: {alumno.email || 'Sin email'}<br />
                        TelÃ©fono: {alumno.telefono || 'Sin telÃ©fono'}<br />
                        Edad: {(alumno.edad !== null && alumno.edad !== undefined) ? `${alumno.edad} aÃ±os` : '-'}
                      </p>
                      
                      <div className="mt-5">
                        {(() => {
                          const plan = alumno.plan_activo;
                          const estado = plan?.estado || 'Sin plan';
                          
                          if (estado === 'ACTIVO') {
                            return (
                              <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4">
                                <p className="text-sm font-bold text-emerald-800">{plan.plan_nombre}</p>
                                <p className="text-sm text-emerald-700 mt-1">{plan.clases_restantes} clases restantes</p>
                                <p className="text-xs text-emerald-600 mt-1">Vence: {plan.fecha_vencimiento}</p>
                              </div>
                            );
                          }
                          
                          if (estado === 'AGOTADO') {
                            return (
                              <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
                                <p className="text-sm font-bold text-amber-800">{plan.plan_nombre}</p>
                                <p className="text-sm text-amber-700 mt-1">Pendiente de renovaciÃ³n (0 clases)</p>
                                <p className="text-xs text-amber-600 mt-1">Vence: {plan.fecha_vencimiento}</p>
                              </div>
                            );
                          }
                          
                          return (
                            <div className="bg-rose-50 border border-rose-100 rounded-xl p-4">
                              <p className="text-sm font-bold text-rose-800">{estado === 'VENCIDO' ? 'Plan Vencido' : 'Sin Plan Activo'}</p>
                            </div>
                          );
                        })()}
                      </div>
                    </CardContent>
                    <div className="p-6 pt-0">
                      <Button variant="outline" className="w-full">
                        Ficha Completa / Asignar Plan
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
            {!loading && alumnos.length === 0 && <p className="text-muted col-span-full">{`No se encontraron ${labelPlural}.`}</p>}
          </div>
        </div>
      )}

      {/* Modal Ficha Completa */}
      <EditStudentModal
        isOpen={!!selectedAlumno}
        onClose={() => setSelectedAlumno(null)}
        alumno={selectedAlumno}
        onUpdate={() => {
          fetchAlumnos();
          setSelectedAlumno(null);
        }}
      />

      {/* Modal Nueva Alumna */}
      <Modal isOpen={showNewModal} onClose={() => setShowNewModal(false)} title={`Nuev@ ${labelSingular}`}>
        <AlumnoForm 
          planes={planes} 
          onSubmit={handleCreateAlumno} 
          onCancel={() => setShowNewModal(false)} 
          isSubmitting={creating} 
          submitLabel={`Crear ${labelSingular}`} 
        />
      </Modal>

      <ConfirmModal
        isOpen={!!alumnoToDelete}
        onClose={() => setAlumnoToDelete(null)}
        onConfirm={() => { if (alumnoToDelete) handleDeleteAlumno(alumnoToDelete); }}
        title={`Eliminar ${labelSingular}`}
        message={`Â¿Seguro que deseas eliminar a est@ ${labelSingular}? Esta acciÃ³n no se puede deshacer.`}
        confirmText="Eliminar"
        isDestructive={true}
      />
    </motion.div>
  );
}
