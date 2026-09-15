/* Developed by FireSeed - Fueling Innovation */
import React, { useState, useEffect } from 'react';
import { Skeleton } from "../../components/ui/Skeleton";
import { toast } from "sonner";
import { useLocation } from 'react-router-dom';
import { api } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';
import { Modal } from '@/components/ui/Modal';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { ProfesorTabHoy } from './ProfesorTabHoy';
import { ProfesorTabMes } from './ProfesorTabMes';
import { ProfesorTabProximos } from './ProfesorTabProximos';
import { ProfesorTabRecurrentes } from './ProfesorTabRecurrentes';
import { ProfesorBolsaTrabajo } from './ProfesorBolsaTrabajo';
import { type ProfesorDashboardData } from '@/types/profesor';


export function ProfesorDashboard() {
  const [data, setData] = useState<ProfesorDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  // Password change state
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [changingPwd, setChangingPwd] = useState(false);
  const [showPast, setShowPast] = useState(false);
  const [activeTab, setActiveTab] = useState('hoy');

  // Assignment states
  const [turnoToAssign, setTurnoToAssign] = useState<string | null>(null);
  const [plantillaToAssign, setPlantillaToAssign] = useState<string | null>(null);
  const [assigningPlantilla, setAssigningPlantilla] = useState(false);

  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  const location = useLocation();
  const hash = location.hash || '#hoy';
  
  // En mobile, el hash controla qué panel grande vemos
  const isMobileHoy = hash === '#hoy';
  const isMobileAgenda = hash === '#agenda';
  const isMobileBolsa = hash === '#bolsa';
  const isMobilePerfil = hash === '#perfil';

  // Si estamos en mobile y en agenda, nos aseguramos de no estar en 'hoy'
  useEffect(() => {
    if (window.innerWidth < 1024) {
      if (isMobileAgenda && activeTab === 'hoy') setActiveTab('proximos');
      if (isMobileHoy) setActiveTab('hoy');
    }
  }, [hash, activeTab]);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/profesor/dashboard/?month=${selectedMonth}&year=${selectedYear}`);
      setData(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Error cargando el panel.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [selectedMonth, selectedYear]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setChangingPwd(true);
    try {
      await api.post('/auth/password/change/', {
        old_password: oldPassword,
        new_password1: newPassword,
        new_password2: newPassword
      });
      toast.success('Contraseña actualizada eééxitosamente');
      setShowPasswordModal(false);
      setOldPassword('');
      setNewPassword('');
    } catch (e: any) {
      toast.error('Error cambiando contraseña. Revisa que la clave actual sea correcta.');
    } finally {
      setChangingPwd(false);
    }
  };

  const confirmAssignPlantilla = async () => {
    if (!plantillaToAssign) return;
    setAssigningPlantilla(true);
    try {
      await api.post(`/profesor/plantillas/${plantillaToAssign}/assign/`);
      toast.success('Horario fijo asignado con éééxito. Ahora aparecerá en tu calendario.');
      setPlantillaToAssign(null);
      fetchDashboard();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Error asignando plantilla');
    } finally {
      setAssigningPlantilla(false);
    }
  };

  const confirmAssignTurno = async () => {
    if (!turnoToAssign) return;
    try {
      await api.post(`/profesor/turnos/${turnoToAssign}/assign/`);
      toast.success('¡Clase asignada eééxitosamente!');
      setTurnoToAssign(null);
      fetchDashboard();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Error asignando la clase');
    }
  };

  const formatFecha = (d: string) => {
    try {
      const dp = d.split('T')[0];
      const [y, m, day] = dp.split('-');
      const date = new Date(parseInt(y), parseInt(m)-1, parseInt(day));
      if (isNaN(date.getTime())) return 'Fecha inválida';
      return new Intl.DateTimeFormat('es-AR', { weekday: 'long', day: 'numeric', month: 'short' }).format(date).replace(/^\w/, c => c.toUpperCase());
    } catch(e) {
      return 'Fecha inválida';
    }
  };

  const formatDayOfWeek = (dow: number) => {
    const days = ['Domingos', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábados'];
    return days[dow % 7];
  };


  

  // Filter turnos_hoy
  const now = new Date();
  const currentHHMM = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
  
  const upcomingHoy = data ? data.turnos_hoy.filter((t: any) => t.hora_fin.slice(0,5) >= currentHHMM) : [];
  const pastHoy = data ? data.turnos_hoy.filter((t: any) => t.hora_fin.slice(0,5) < currentHHMM) : [];
  const displayHoy = showPast ? [...upcomingHoy, ...pastHoy].sort((a: any, b: any) => a.hora_inicio.localeCompare(b.hora_inicio)) : upcomingHoy;

  return (
    <AnimatePresence mode="wait">
      {loading ? (
        <motion.div 
          key="skeleton"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="p-8 space-y-6"
        >
          <div className="h-12 w-1/4 mb-8 bg-primary-light rounded-2xl animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="h-48 w-full bg-primary-light/50 rounded-2xl animate-pulse"></div>
            <div className="h-48 w-full bg-primary-light/50 rounded-2xl animate-pulse"></div>
            <div className="h-48 w-full bg-primary-light/50 rounded-2xl animate-pulse"></div>
          </div>
        </motion.div>
      ) : !data ? (
        <motion.p key="error" className="text-muted p-4">Error cargando el panel.</motion.p>
      ) : (
        <motion.div 
          key="content"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className="space-y-8"
        >
      
      {/* Header & Stats - Desktop only */}
      <div className="hidden lg:flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          {/* Apple-style Segmented Control for Tabs */}
          <div className="bg-primary-light/50 p-1 rounded-2xl w-fit relative z-10 overflow-x-auto max-w-full flex">
            {['hoy', 'mes', 'proximos', 'recurrentes'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`relative px-4 py-2.5 text-sm font-semibold rounded-xl transition-colors whitespace-nowrap ${activeTab === tab ? 'text-primary-main' : 'text-primary-main/70 hover:text-primary-hover'}`}
              >
                {activeTab === tab && (
                  <motion.div
                    layoutId="profesorTab"
                    className="absolute inset-0 bg-white rounded-xl shadow-sm z-0"
                    transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                  />
                )}
                <span className="relative z-10">
                  {tab === 'hoy' && 'Clases de Hoy'}
                  {tab === 'mes' && 'Dictadas en el Mes'}
                  {tab === 'proximos' && 'Próximos Días'}
                  {tab === 'recurrentes' && 'Mis Clases Recurrentes'}
                </span>
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex shrink-0">
          <Button variant="outline" size="sm" onClick={() => setShowPasswordModal(true)}>
            Cambiar Contraseña
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Desktop View: activeTab dictates what is shown in the left column */}
        <div className="hidden lg:block lg:col-span-2 space-y-6">
          <AnimatePresence mode="wait">
            {activeTab === 'hoy' && <ProfesorTabHoy data={data} formatFecha={formatFecha} />}
            {activeTab === 'mes' && (
              <ProfesorTabMes 
                data={data} 
                selectedMonth={selectedMonth} 
                setSelectedMonth={setSelectedMonth} 
                selectedYear={selectedYear} 
                setSelectedYear={setSelectedYear} 
                formatFecha={formatFecha} 
              />
            )}
            {activeTab === 'proximos' && (
              <ProfesorTabProximos 
                data={data} 
                formatFecha={formatFecha} 
                showPast={showPast} 
                setShowPast={setShowPast} 
              />
            )}
            {activeTab === 'recurrentes' && <ProfesorTabRecurrentes data={data} />}
          </AnimatePresence>
        </div>

        {/* Mobile View: Hash dictates what is shown */}
        <div className="block lg:hidden space-y-6 w-full">
           {isMobileHoy && <ProfesorTabHoy data={data} formatFecha={formatFecha} />}
           {isMobileAgenda && (
             <div className="space-y-8">
               <ProfesorTabProximos 
                 data={data} 
                 formatFecha={formatFecha} 
                 showPast={showPast} 
                 setShowPast={setShowPast} 
               />
               <div className="border-t border-primary-light/40 pt-4"></div>
               <ProfesorTabRecurrentes data={data} />
             </div>
           )}
           {isMobilePerfil && (
             <div className="space-y-8">
               <ProfesorTabMes 
                 data={data} 
                 selectedMonth={selectedMonth} 
                 setSelectedMonth={setSelectedMonth} 
                 selectedYear={selectedYear} 
                 setSelectedYear={setSelectedYear} 
                 formatFecha={formatFecha} 
               />
               <div className="flex flex-col w-full space-y-4 pt-6 border-t border-primary-light/50">
                 <Button variant="outline" size="sm" onClick={() => setShowPasswordModal(true)} className="w-full">
                   Cambiar Contraseña
                 </Button>
                 <Button variant="default" className="w-full bg-rose-600 hover:bg-rose-700 text-white" onClick={async () => {
                   const baseUrl = import.meta.env.BASE_URL || '/';
                   const loginPath = baseUrl.endsWith('/') ? baseUrl + 'login' : baseUrl + '/login';
                   try {
                     await api.post('/auth/logout/');
                   } finally {
                     window.location.href = loginPath;
                   }
                 }}>
                   Cerrar Sesión
                 </Button>
               </div>
             </div>
           )}
        </div>

        {/* Right Column: Bolsa de Trabajo */}
        <div className={`lg:sticky lg:top-24 flex-col h-[calc(100vh-8rem)] ${isMobileBolsa ? 'flex' : 'hidden lg:flex'}`}>
          <div className="pb-4 mb-4 border-b border-primary-light shrink-0">
            <h3 className="text-xl font-bold text-primary-main flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violett-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-primary-light/500"></span>
              </span>
              Bolsa de Horarios Libres
            </h3>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <section className="space-y-4 pb-8">

            {data.plantillas_libres.length === 0 && data.turnos_libres.length === 0 ? (
              <Card className="bg-primary-light/50 border-none">
                <CardContent className="py-8 text-center text-muted">
                  No hay clases buscando profesor en este momento.
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                <AnimatePresence mode="popLayout">
                  {data.plantillas_libres.map((p: any) => (
                    <motion.div key={p.id} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}>
                      <Card className="border-primary-light shadow-sm overflow-hidden relative">
                        <div className="absolute top-0 right-0 bg-primary-light text-primary-hover text-[10px] font-bold px-2 py-1 rounded-bl-lg uppercase tracking-wider">
                          Fijo Semanal
                        </div>
                        <CardContent className="p-4 pt-6">
                          <p className="font-bold text-foreground">Todos los {formatDayOfWeek(p.dia_semana)}</p>
                          <p className="text-sm text-muted">{p.hora_inicio.slice(0,5)} hs</p>
                          <div className="mt-3 flex justify-between items-end">
                            <div>
                              <p className="text-primary-hover font-medium">{p.clase_nombre}</p>
                            </div>
                            <Button 
                              size="sm" 
                              onClick={() => setPlantillaToAssign(p.id)}
                              variant="default"
                            >
                              Tomar horario
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}

                  {data.turnos_libres.map((t: any) => (
                    <motion.div key={t.id} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}>
                      <Card className="border-gray-200 shadow-sm overflow-hidden relative">
                        <div className="absolute top-0 right-0 bg-gray-100 text-gray-600 text-[10px] font-bold px-2 py-1 rounded-bl-lg uppercase tracking-wider">
                          Puntual
                        </div>
                        <CardContent className="p-4 pt-6">
                          <p className="font-bold text-foreground">{formatFecha(t.fecha)}</p>
                          <p className="text-sm text-muted">{t.hora_inicio.slice(0,5)} hs</p>
                          <div className="mt-3 flex justify-between items-end">
                            <div>
                              <p className="text-primary-hover font-medium">{t.clase_nombre}</p>
                            </div>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => setTurnoToAssign(t.id)}
                            >
                              Tomar clase
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
            </section>
          </div>
        </div>
      </div>

      <Modal isOpen={showPasswordModal} onClose={() => setShowPasswordModal(false)} title="Cambiar Contraseña">
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">Contraseña Actual</label>
            <input 
              type="password" 
              required 
              value={oldPassword} 
              onChange={e => setOldPassword(e.target.value)} 
              className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" 
            />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1 text-foreground">Nueva Contraseña</label>
            <input 
              type="password" 
              required 
              minLength={8}
              value={newPassword} 
              onChange={e => setNewPassword(e.target.value)} 
              className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" 
            />
          </div>
          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-primary-light">
            <Button type="button" variant="outline" onClick={() => setShowPasswordModal(false)}>Cancelar</Button>
            <Button type="submit" disabled={changingPwd}>
              {changingPwd ? 'Cambiando...' : 'Cambiar Contraseña'}
            </Button>
          </div>
        </form>
      </Modal>

      <ConfirmModal
        isOpen={!!plantillaToAssign}
        onClose={() => setPlantillaToAssign(null)}
        onConfirm={confirmAssignPlantilla}
        title="Tomar Horario Fijo"
        message="¿Confirmas que deseas tomar este horario fijo semanal? Se te asignarán automáticamente todas las clases futuras."
        confirmText="Sí, tomar horario"
      />

      <ConfirmModal
        isOpen={!!turnoToAssign}
        onClose={() => setTurnoToAssign(null)}
        onConfirm={confirmAssignTurno}
        title="Tomar Clase Puntual"
        message="¿Estás seguro de que quieres dar esta clase?"
        confirmText="Sí, tomar clase"
      />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

