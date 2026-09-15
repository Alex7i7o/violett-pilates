import React, { useState, useEffect } from 'react';
import { Modal } from '../../../components/ui/Modal';
import { ConfirmModal } from '../../../components/ui/ConfirmModal';
import { Button } from '../../../components/ui/Button';
import { api } from '../../../lib/api';
import { deleteAdminAlumno } from '../../../lib/adminApi';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, Plus, Minus } from 'lucide-react';
import { useClientConfig } from '../../../context/ClientConfigContext';

interface EditStudentModalProps {
  isOpen: boolean;
  onClose: () => void;
  alumno: any;
  onUpdate: () => void;
}

export function EditStudentModal({ isOpen, onClose, alumno: rawAlumno, onUpdate }: EditStudentModalProps) {
  const [activeTab, setActiveTab] = useState<'perfil' | 'plan' | 'fijos'>('perfil');
  const prevAlumnoRef = React.useRef<any>(null);
  React.useEffect(() => {
    if (rawAlumno) {
      prevAlumnoRef.current = rawAlumno;
    }
  }, [rawAlumno]);
  const alumno = rawAlumno || prevAlumnoRef.current;

  const [loading, setLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Perfil State
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [apellido, setApellido] = useState('');
  const [telefono, setTelefono] = useState('');

  // Plan State
  const [planes, setPlanes] = useState<any[]>([]);
  // Estética Wallets
  const config = useClientConfig();
  const isEstetica = config.client_id === 'violett_estetica';
  const [billeteras, setBilleteras] = useState<any[]>([]);
  const [servicios, setServicios] = useState<any[]>([]);
  const [selectedServicio, setSelectedServicio] = useState('');
  const [cantidadToAdd, setCantidadToAdd] = useState(1);

  const [selectedPlanId, setSelectedPlanId] = useState('');
  const [clasesRestantes, setClasesRestantes] = useState<number>(0);
  
  // Recurrencias State
  const [recurrencias, setRecurrencias] = useState<any[]>([]);
  const [clases, setClases] = useState<any[]>([]);
  const [newRecClase, setNewRecClase] = useState('');
  const [newRecDia, setNewRecDia] = useState('1');
  const [newRecHora, setNewRecHora] = useState('09:00');
  const [recurrenciaToDelete, setRecurrenciaToDelete] = useState<number | null>(null);

  useEffect(() => {
    if (alumno && isOpen) {
      setNombre(alumno.nombre || '');
      setEmail(alumno.email || '');
      setApellido(alumno.apellido || '');
      setTelefono(alumno.telefono || '');
      if (isEstetica && alumno.id) {
        api.get('/billeteras/').then(res => {
          setBilleteras(res.data.filter((b: any) => b.usuario === alumno.id));
        }).catch(console.error);
        api.get('/servicios/').then(res => setServicios(res.data)).catch(console.error);
      }

      
      const planActivo = alumno.plan_activo;
      if (planActivo) {
        setClasesRestantes(planActivo.clases_restantes);
      } else {
        setClasesRestantes(0);
      }

      fetchPlanes();
      fetchRecurrencias();
      fetchClases();
      setActiveTab('perfil');
    }
  }, [alumno, isOpen]);

  const fetchPlanes = async () => {
    try {
      const res = await api.get('/admin/planes/');
      setPlanes(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchClases = async () => {
    try {
      const res = await api.get('/admin/clases/');
      setClases(res.data);
      if (res.data.length > 0) setNewRecClase(res.data[0].id);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchRecurrencias = async () => {
    try {
      const res = await api.get(`/admin/alumnos/${alumno.id}/recurrencias/`);
      setRecurrencias(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteAlumno = async () => {
    try {
      setLoading(true);
      await deleteAdminAlumno(alumno.id);
      toast.success(isEstetica ? "Paciente eliminado" : "Alumna eliminada");
      setShowDeleteConfirm(false);
      onClose();
      onUpdate();
    } catch(e) {
      toast.error("Error al eliminar");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePerfil = async () => {
    setLoading(true);
    try {
      await api.patch(`/admin/alumnos/${alumno.id}/`, {
        nombre,
        apellido,
        telefono,
        email
      });
      toast.success('Perfil actualizado');
      onUpdate();
    } catch (e) {
      toast.error('Error al actualizar perfil');
    } finally {
      setLoading(false);
    }
  };

  const handleAsignarPlan = async () => {
    if (!selectedPlanId) return toast.error('Seleccione un plan');
    setLoading(true);
    try {
      await api.post(`/admin/alumnos/${alumno.id}/asignar-plan/`, {
        plan_id: selectedPlanId
      });
      toast.success('Plan asignado correctamente');
      onUpdate();
      onClose();
    } catch (e) {
      toast.error('Error al asignar plan');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateClases = async () => {
    const planActivo = alumno.plan_activo;
    if (!planActivo) return;
    setLoading(true);
    try {
      await api.patch(`/admin/suscripciones/${planActivo.id}/`, {
        clases_restantes: clasesRestantes
      });
      toast.success('Clases actualizadas');
      onUpdate();
    } catch (e) {
      toast.error('Error al actualizar clases');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRecurrencia = async () => {
    setLoading(true);
    try {
      await api.post(`/admin/alumnos/${alumno.id}/recurrencias/`, {
        clase_id: newRecClase,
        dia_semana: parseInt(newRecDia),
        hora_inicio: newRecHora
      });
      toast.success('Horario fijo asignado');
      fetchRecurrencias();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Error al asignar');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRecurrencia = async (id: string) => {
    
    try {
      await api.delete(`/admin/alumnos/${alumno.id}/recurrencias/${id}/`);
      toast.success('Horario eliminado');
      fetchRecurrencias();
    } catch (e) {
      toast.error('Error al eliminar');
    }
  };

  const getDiaName = (num: number) => {
    const d = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    return d[num - 1] || '';
  };

  if (!alumno) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Editar Alumno">
      <div className="flex border-b mb-4">
        <button 
          className={`flex-1 py-2 text-sm font-semibold border-b-2 transition-colors ${activeTab === 'perfil' ? 'border-primary-main text-primary-main' : 'border-transparent text-muted'}`}
          onClick={() => setActiveTab('perfil')}
        >Perfil</button>
        <button 
          className={`flex-1 py-2 text-sm font-semibold border-b-2 transition-colors ${activeTab === 'plan' ? 'border-primary-main text-primary-main' : 'border-transparent text-muted'}`}
          onClick={() => setActiveTab('plan')}
        >{isEstetica ? 'Billeteras' : 'Plan'}</button>
        <button 
          className={`flex-1 py-2 text-sm font-semibold border-b-2 transition-colors ${activeTab === 'fijos' ? 'border-primary-main text-primary-main' : 'border-transparent text-muted'}`}
          onClick={() => setActiveTab('fijos')}
        >Horarios Fijos</button>
      </div>

      <div className="space-y-4 max-h-[60vh] overflow-y-auto px-1">
        {activeTab === 'perfil' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Nombre</label>
              <input type="text" value={nombre} onChange={e => setNombre(e.target.value)} className="w-full p-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Apellido</label>
              <input type="text" value={apellido} onChange={e => setApellido(e.target.value)} className="w-full p-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Teléfono</label>
              <input type="text" value={telefono} onChange={e => setTelefono(e.target.value)} className="w-full p-2 border rounded-lg" />
            </div>
                          <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value.toLowerCase())} className="w-full p-2 border rounded-lg" />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleUpdatePerfil} disabled={loading} className="flex-1">Guardar Perfil</Button>
                <Button onClick={() => setShowDeleteConfirm(true)} variant="outline" className="text-red-500 border-red-200 hover:bg-red-50 hover:text-red-600 px-3 transition-colors" title={isEstetica ? "Eliminar Paciente" : "Eliminar Alumno"}>
                  <Trash2 size={20} />
                </Button>
              </div>
          </div>
        )}

        
          {activeTab === 'plan' && isEstetica && (
              <div className="space-y-6">
                <h3 className="font-bold text-lg text-neutral-800">Billeteras (Créditos)</h3>
                
                <div className="bg-neutral-50 p-4 rounded-xl border border-neutral-200 flex gap-2 items-end">
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-neutral-600 mb-1">Servicio a acreditar</label>
                    <select value={selectedServicio} onChange={e => setSelectedServicio(e.target.value)} className="w-full p-2 border rounded-lg">
                      <option value="">Seleccionar...</option>
                      {servicios.map(s => <option key={s.id} value={s.id}>{s.nombre}</option>)}
                    </select>
                  </div>
                  <div className="w-24">
                    <label className="block text-xs font-medium text-neutral-600 mb-1">Sesiones</label>
                    <input type="number" min={1} value={cantidadToAdd} onChange={e => setCantidadToAdd(parseInt(e.target.value)||1)} className="w-full p-2 border rounded-lg" />
                  </div>
                  <Button onClick={handleAddBilletera} className="shrink-0 h-[38px] px-4">Acreditar</Button>
                </div>

                <div className="space-y-3">
                  {billeteras.map(bill => {
                    const servicio = servicios.find(s => s.id === bill.servicio)?.nombre || 'Servicio borrado';
                    return (
                      <div key={bill.id} className="flex items-center justify-between p-3 rounded-lg border border-neutral-100 bg-white shadow-sm">
                        <div>
                          <p className="font-semibold text-neutral-800">{servicio}</p>
                          <p className="text-xs text-neutral-500">Vence: {bill.fecha_vencimiento} • {bill.estado}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <button onClick={() => handleUpdateBilletera(bill.id, bill.sesiones_restantes, -1)} className="w-8 h-8 rounded-full bg-neutral-100 flex items-center justify-center hover:bg-red-100 hover:text-red-600 transition-colors"><Minus size={16} /></button>
                          <span className="font-bold text-lg min-w-[20px] text-center">{bill.sesiones_restantes}</span>
                          <button onClick={() => handleUpdateBilletera(bill.id, bill.sesiones_restantes, 1)} className="w-8 h-8 rounded-full bg-neutral-100 flex items-center justify-center hover:bg-green-100 hover:text-green-600 transition-colors"><Plus size={16} /></button>
                        </div>
                      </div>
                    )
                  })}
                  {billeteras.length === 0 && <p className="text-center text-sm text-neutral-500">No tiene billeteras activas.</p>}
                </div>
              </div>
          )}
          {activeTab === 'plan' && !isEstetica && (
          <div className="space-y-6">
            <div className="p-4 bg-primary-light/30 rounded-xl space-y-3 border">
              <h4 className="font-semibold text-primary-main">Asignar Nuevo Plan</h4>
              <p className="text-xs text-muted">Esto reemplazará el plan actual del alumno.</p>
              <select className="w-full p-2 border rounded-lg" value={selectedPlanId} onChange={e => setSelectedPlanId(e.target.value)}>
                <option value="">Seleccione un plan...</option>
                {planes.map(p => <option key={p.id} value={p.id}>{p.nombre} ({p.cantidad_clases} clases)</option>)}
              </select>
              <Button onClick={handleAsignarPlan} disabled={loading} variant="outline" className="w-full">Asignar Plan</Button>
            </div>

            {alumno.plan_activo && (
              <div className="p-4 bg-emerald-50 rounded-xl space-y-3 border border-emerald-100">
                <h4 className="font-semibold text-emerald-800">Plan Actual: {alumno.plan_activo.plan_nombre}</h4>
                <div>
                  <label className="block text-sm font-medium mb-1 text-emerald-900">Modificar Clases Restantes</label>
                  <div className="flex gap-2">
                    <input type="number" value={clasesRestantes} onChange={e => setClasesRestantes(parseInt(e.target.value))} className="w-full p-2 border rounded-lg" />
                    <Button onClick={handleUpdateClases} disabled={loading}>Actualizar</Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'fijos' && (
          <div className="space-y-6">
            <div className="space-y-3">
              <h4 className="font-semibold">Horarios fijos actuales</h4>
              {recurrencias.length === 0 ? <p className="text-sm text-muted">No tiene horarios fijos.</p> : (
                <div className="space-y-2">
                  {recurrencias.map(r => (
                    <div key={r.id} className="flex justify-between items-center p-3 bg-gray-50 border rounded-lg">
                      <div>
                        <p className="font-medium text-sm">{r.clase_nombre}</p>
                        <p className="text-xs text-muted">Todos los {getDiaName(r.dia_semana)} a las {r.hora_inicio} hs</p>
                      </div>
                      <button onClick={() => setRecurrenciaToDelete(r.id)} className="text-red-500 p-2 hover:bg-red-50 rounded-lg">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-4 bg-primary-light/30 rounded-xl space-y-3 border mt-4">
              <h4 className="font-semibold text-primary-main">Agregar nuevo horario fijo</h4>
              <select className="w-full p-2 border rounded-lg text-sm" value={newRecClase} onChange={e => setNewRecClase(e.target.value)}>
                {clases.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
              </select>
              <div className="flex gap-2">
                <select className="w-1/2 p-2 border rounded-lg text-sm" value={newRecDia} onChange={e => setNewRecDia(e.target.value)}>
                  <option value="1">Lunes</option>
                  <option value="2">Martes</option>
                  <option value="3">Miércoles</option>
                  <option value="4">Jueves</option>
                  <option value="5">Viernes</option>
                  <option value="6">Sábado</option>
                  <option value="7">Domingo</option>
                </select>
                <input type="time" className="w-1/2 p-2 border rounded-lg text-sm" value={newRecHora} onChange={e => setNewRecHora(e.target.value)} />
              </div>
              <Button onClick={handleAddRecurrencia} disabled={loading || !newRecClase} className="w-full">Agregar</Button>
            </div>
          </div>
        )}
      </div>

      <ConfirmModal
        isOpen={!!recurrenciaToDelete}
        onClose={() => setRecurrenciaToDelete(null)}
        onConfirm={() => {
          if (recurrenciaToDelete) {
            handleDeleteRecurrencia(recurrenciaToDelete);
            setRecurrenciaToDelete(null);
          }
        }}
        title="Eliminar Horario Fijo"
        message="¿Seguro que deseas eliminar este horario fijo para el alumno? Esto cancelará todas sus reservas futuras asociadas a este horario."
        confirmText="Sí, eliminar"
      />

      <ConfirmModal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDeleteAlumno}
        title={isEstetica ? "Eliminar Paciente" : "Eliminar Alumna"}
        message={isEstetica ? "¿Estás segura de que deseas eliminar este paciente? Esta acción no se puede deshacer y borrará sus billeteras y turnos." : "¿Estás segura de que deseas eliminar esta alumna? Esta acción no se puede deshacer y borrará su plan y turnos."}
        confirmText="Sí, eliminar"
        cancelText="Cancelar"
        isDestructive={true}
      />
    </Modal>
  );
}