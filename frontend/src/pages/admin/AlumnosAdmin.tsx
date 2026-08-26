import React, { useState, useEffect } from 'react';
import { toast } from "sonner";
import { getAdminAlumnos, createAdminAlumno, asignarPlanAlumno } from '../../lib/adminApi';
import type { UsuarioAdmin } from '../../lib/adminApi';
import { api } from '../../lib/api';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { AlumnoForm, type AlumnoFormData } from '../../components/admin/AlumnoForm';
import { Modal } from '../../components/ui/Modal';
import { Badge } from '../../components/ui/Badge';
import { InputField } from '../../components/ui/InputField';
import { SelectField } from '../../components/ui/SelectField';
import { motion, AnimatePresence } from 'framer-motion';

export function AlumnosAdmin() {
  const [alumnos, setAlumnos] = useState<UsuarioAdmin[]>([]);
  const [search, setSearch] = useState('');
  const [minAge, setMinAge] = useState('');
  const [maxAge, setMaxAge] = useState('');
  const [estadoFilter, setEstadoFilter] = useState('Todos');
  const [loading, setLoading] = useState(false);
  
  const [selectedAlumno, setSelectedAlumno] = useState<UsuarioAdmin | null>(null);
  const [planes, setPlanes] = useState<any[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState('');
  const [assigning, setAssigning] = useState(false);

  // Nuevo Alumno Modal State
  const [showNewModal, setShowNewModal] = useState(false);
    const [newApellido, setNewApellido] = useState('');
      const [newContacto, setNewContacto] = useState('');
    const [newFechaNacimiento, setNewFechaNacimiento] = useState('');
  const [newSexo, setNewSexo] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchAlumnos = async () => {
    setLoading(true);
    try {
      const res = await getAdminAlumnos(search);
      setAlumnos(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlanes = async () => {
    try {
      const res = await api.get('/admin/planes/');
      setPlanes(res.data);
      if (res.data.length > 0) setSelectedPlanId(res.data[0].id);
    } catch (e) {
      console.error("Error fetching planes", e);
    }
  }

  useEffect(() => {
    fetchPlanes();
  }, []);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchAlumnos();
    }, 300);
    return () => clearTimeout(delayDebounceFn);
  }, [search]);

  const handleAssignPlan = async () => {
    if (!selectedAlumno || !selectedPlanId) return;
    setAssigning(true);
    try {
      await asignarPlanAlumno(selectedAlumno.id, selectedPlanId);
      toast.success('Plan asignado correctamente. El plan anterior ha sido vencido.')
      setSelectedAlumno(null);
      fetchAlumnos();
    } catch (e) {
      toast.error('Error asignando plan')
    } finally {
      setAssigning(false);
    }
  }

    const handleCreateAlumno = async (data: AlumnoFormData) => {
    setCreating(true);
    try {
      await api.post('/admin/alumnos/', data);
      toast.success('Alumna creada exitosamente');
      fetchData();
      setShowNewModal(false);
    } catch (e: any) {
      console.error(e);
      toast.error('Error al crear alumna. ' + (e.response?.data?.detail || ''));
    } finally {
      setCreating(false);
    }
  };

  const filteredAlumnos = alumnos.filter(a => {
    if (minAge && (a.edad === null || a.edad < parseInt(minAge))) return false;
    if (maxAge && (a.edad === null || a.edad > parseInt(maxAge))) return false;
    if (estadoFilter !== 'Todos') {
      const estadoCalculado = a.plan_activo?.estado_calculado || 'Sin plan';
      if (estadoFilter !== estadoCalculado) return false;
    }
    return true;
  });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h2 className="text-3xl font-bold text-violett-900">Directorio de Alumnas</h2>
        <Button onClick={() => setShowNewModal(true)}>+ Nueva Alumna</Button>
      </div>

      <Card>
        <CardContent className="pt-6">
          <input 
            type="text"
            placeholder="Buscar por nombre, apellido o teléfono..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full max-w-xl p-3 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 shadow-sm"
          />
        </CardContent>
      </Card>

      {loading ? (
        <p className="text-muted py-4">Buscando...</p>
      ) : (
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
                <Card className="h-full flex flex-col justify-between hover:shadow-glow transition-shadow">
                  <CardContent className="pt-6">
                    <h3 className="text-xl font-bold text-foreground">{alumno.nombre} {alumno.apellido}</h3>
                    <p className="text-sm text-muted mt-1">
                      Tel: {alumno.telefono || 'Sin teléfono'} • Edad: {alumno.edad !== null ? `${alumno.edad} años` : '-'}
                    </p>
                    
                    <div className="mt-5">
                      {(() => {
                        const plan = alumno.plan_activo;
                        const estado = plan?.estado_calculado || 'Sin plan';
                        
                        if (estado === 'Activo') {
                          return (
                            <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4">
                              <p className="text-sm font-bold text-emerald-800">{plan!.nombre}</p>
                              <p className="text-sm text-emerald-700 mt-1">{plan!.clases_restantes} clases restantes</p>
                              <p className="text-xs text-emerald-600 mt-1">Vence: {plan!.fecha_vencimiento}</p>
                            </div>
                          );
                        }
                        
                        if (estado === 'Pendiente') {
                          return (
                            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
                              <p className="text-sm font-bold text-amber-800">{plan!.nombre}</p>
                              <p className="text-sm text-amber-700 mt-1">Pendiente de renovación (0 clases)</p>
                              <p className="text-xs text-amber-600 mt-1">Vence: {plan!.fecha_vencimiento}</p>
                            </div>
                          );
                        }
                        
                        return (
                          <div className="bg-rose-50 border border-rose-100 rounded-xl p-4">
                            <p className="text-sm font-bold text-rose-800">Sin Plan Activo</p>
                          </div>
                        );
                      })()}
                    </div>
                  </CardContent>
                  <div className="p-6 pt-0">
                    <Button variant="outline" className="w-full" onClick={() => setSelectedAlumno(alumno)}>
                      Ficha Completa / Asignar Plan
                    </Button>
                  </div>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
          {!loading && alumnos.length === 0 && <p className="text-muted col-span-full">No se encontraron alumnas.</p>}
        </div>
      )}

      {/* Modal Ficha Completa */}
      <Modal isOpen={!!selectedAlumno} onClose={() => setSelectedAlumno(null)} title="Ficha de Alumna">
        {selectedAlumno && (
          <div className="space-y-6">
            <div>
              <h4 className="text-2xl font-bold text-foreground mb-1">{selectedAlumno.nombre} {selectedAlumno.apellido}</h4>
              <p className="text-muted">{selectedAlumno.email}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-violett-50 p-4 rounded-xl border border-violett-100">
                <span className="block text-xs text-violett-600 uppercase font-bold tracking-wider mb-1">Teléfono</span>
                <span className="text-foreground font-medium">{selectedAlumno.telefono || '-'}</span>
              </div>
              <div className="bg-violett-50 p-4 rounded-xl border border-violett-100">
                <span className="block text-xs text-violett-600 uppercase font-bold tracking-wider mb-1">Emergencia</span>
                <span className="text-foreground font-medium">{selectedAlumno.contacto_emergencia || '-'}</span>
              </div>
              <div className="bg-violett-50 p-4 rounded-xl border border-violett-100 col-span-2">
                <span className="block text-xs text-violett-600 uppercase font-bold tracking-wider mb-1">Notas Médicas</span>
                <span className="text-foreground font-medium">{selectedAlumno.notas_medicas || '-'}</span>
              </div>
            </div>

            <div className="border-t border-violett-100 pt-6">
              <h5 className="font-bold text-foreground mb-4">Carga Manual de Plan (Pago Físico)</h5>
              <div className="flex gap-3">
                <select 
                  value={selectedPlanId} 
                  onChange={e => setSelectedPlanId(e.target.value)}
                  className="flex-1 p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white"
                >
                  {planes.map(p => (
                    <option key={p.id} value={p.id}>{p.nombre} ({p.cantidad_clases} clases)</option>
                  ))}
                </select>
                <Button onClick={handleAssignPlan} disabled={assigning}>
                  {assigning ? 'Cargando...' : 'Asignar'}
                </Button>
              </div>
              <p className="text-xs text-muted mt-3">
                * Asignar un plan nuevo sobreescribirá cualquier plan activo que tenga la alumna.
              </p>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal Nueva Alumna */}
      <Modal isOpen={showNewModal} onClose={() => setShowNewModal(false)} title="Nueva Alumna">
        <AlumnoForm 
          planes={planes} 
          onSubmit={handleCreateAlumno} 
          onCancel={() => setShowNewModal(false)} 
          isSubmitting={creating} 
          submitLabel="Crear Alumna" 
        />
      </Modal>
    </motion.div>
  );
}




