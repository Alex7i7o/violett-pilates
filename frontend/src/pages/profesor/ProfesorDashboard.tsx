/* Developed by FireSeed - Fueling Innovation */
import React, { useState, useEffect } from 'react';
import { Skeleton } from "../../components/ui/Skeleton";
import { toast } from "sonner";
import { api } from '../../lib/api';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';
import { Modal } from '../../components/ui/Modal';
import { ConfirmModal } from '../../components/ui/ConfirmModal';

export function ProfesorDashboard() {
  const [data, setData] = useState<any>(null);
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
      toast.success('Contraseña actualizada exitosamente');
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
      toast.success('Horario fijo asignado con éxito. Ahora aparecerá en tu calendario.');
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
      toast.success('¡Clase asignada exitosamente!');
      setTurnoToAssign(null);
      fetchDashboard();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Error asignando la clase');
    }
  };

  const formatFecha = (d: string) => {
    const [y, m, day] = d.split('-');
    const date = new Date(parseInt(y), parseInt(m)-1, parseInt(day));
    return new Intl.DateTimeFormat('es-AR', { weekday: 'long', day: 'numeric', month: 'short' }).format(date).replace(/^\w/, c => c.toUpperCase());
  };

  const formatDayOfWeek = (dow: number) => {
    const days = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    return days[dow % 7];
  };

  if (loading) return (
    <div className="p-8 space-y-6">
      <Skeleton className="h-12 w-1/4 mb-8" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    </div>
  );
  if (!data) return <p className="text-muted p-4">Error cargando el panel.</p>;

  // Filter turnos_hoy
  const now = new Date();
  const currentHHMM = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
  
  const upcomingHoy = data.turnos_hoy.filter((t: any) => t.hora_fin.slice(0,5) >= currentHHMM);
  const pastHoy = data.turnos_hoy.filter((t: any) => t.hora_fin.slice(0,5) < currentHHMM);
  const displayHoy = showPast ? [...upcomingHoy, ...pastHoy].sort((a: any, b: any) => a.hora_inicio.localeCompare(b.hora_inicio)) : upcomingHoy;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
      
      {/* Header & Stats */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-violett-900 mb-6">Hola, Profesor</h2>
          
          {/* Apple-style Segmented Control for Tabs */}
          <div className="flex bg-violett-100/50 p-1 rounded-2xl w-fit relative z-10 overflow-x-auto max-w-full">
            {['hoy', 'mes', 'proximos', 'recurrentes'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`relative px-4 py-2.5 text-sm font-semibold rounded-xl transition-colors whitespace-nowrap ${activeTab === tab ? 'text-violett-900' : 'text-violett-600/70 hover:text-violett-800'}`}
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
        
        <Button variant="outline" size="sm" onClick={() => setShowPasswordModal(true)} className="ml-4 shrink-0">
          Contraseña
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Agenda (Hoy y Semana) */}
                {/* Left Column: Contenido por Tab */}
        <div className="lg:col-span-2 space-y-6">
          <AnimatePresence mode="wait">
            {activeTab === 'hoy' && (
              <motion.div key="hoy" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
                <section>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-foreground">Clases de Hoy</h3>
              {pastHoy.length > 0 && (
                <Button variant="outline" size="sm" onClick={() => setShowPast(!showPast)}>
                  {showPast ? 'Ocultar clases dadas' : 'Ver clases dadas'}
                </Button>
              )}
            </div>
            
            {displayHoy.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted">
                  No tienes más clases para hoy.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                <AnimatePresence>
                  {displayHoy.map((t: any) => {
                    const isPast = t.hora_fin.slice(0,5) < currentHHMM;
                    return (
                      <motion.div key={t.id} initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                        <Card className={`border-l-4 ${isPast ? 'border-l-gray-400 opacity-60' : 'border-l-violett-600'}`}>
                          <CardContent className="flex justify-between items-center p-4">
                            <div>
                              <p className="font-bold text-foreground text-lg">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)}</p>
                              <p className={`${isPast ? 'text-gray-600' : 'text-violett-900'} font-medium`}>{t.clase_nombre}</p>
                            </div>
                            <Badge variant="default" className={`${isPast ? 'bg-gray-200 text-gray-700' : 'bg-violett-100 text-violett-900'} border-none`}>
                              {isPast ? 'Dada' : `${t.cupo_actual} cupos libres`}
                            </Badge>
                          </CardContent>
                        </Card>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            )}
          </section>
              </motion.div>
            )}
            
            {activeTab === 'mes' && (
              <motion.div key="mes" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
                <div className="bg-white border border-violett-100 px-6 py-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm">
                  <div>
                    <h3 className="text-lg font-bold text-violett-900 mb-3">Filtro de Historial</h3>
                    <div className="flex items-center gap-3">
                      <select 
                        className="border border-violett-200 rounded-xl px-3 py-2 text-sm bg-white text-violett-900 focus:outline-none focus:ring-2 focus:ring-violett-500"
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(Number(e.target.value))}
                      >
                        {Array.from({ length: 12 }, (_, i) => (
                          <option key={i+1} value={i+1}>
                            {new Date(2000, i).toLocaleString('es-ES', { month: 'long' }).replace(/^\w/, c => c.toUpperCase())}
                          </option>
                        ))}
                      </select>
                      <select 
                        className="border border-violett-200 rounded-xl px-3 py-2 text-sm bg-white text-violett-900 focus:outline-none focus:ring-2 focus:ring-violett-500"
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(Number(e.target.value))}
                      >
                        {[new Date().getFullYear() - 1, new Date().getFullYear(), new Date().getFullYear() + 1].map(y => (
                          <option key={y} value={y}>{y}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  <div className="bg-violett-50 px-5 py-3 rounded-xl flex items-center gap-4">
                    <div className="w-10 h-10 bg-violett-900 rounded-full flex items-center justify-center text-white text-lg font-bold shadow-soft">
                      {data.horas_mes}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-violett-900 uppercase tracking-wider">Clases Dictadas</p>
                      <p className="text-xs text-violett-600">En este mes</p>
                    </div>
                  </div>
                </div>
                <section>
            <h3 className="text-xl font-bold text-foreground mb-4">Clases Dictadas en el Mes</h3>
            {(!data.turnos_mes_historial || data.turnos_mes_historial.length === 0) ? (
              <Card>
                <CardContent className="py-8 text-center text-muted">
                  No hay clases dictadas en este mes.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {data.turnos_mes_historial.map((t: any) => (
                  <Card key={t.id} className="border-l-4 border-l-violett-600">
                    <CardContent className="flex justify-between items-center p-4">
                      <div>
                        <p className="font-bold text-foreground">{formatFecha(t.fecha)}</p>
                        <p className="text-muted text-sm">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)} hs</p>
                      </div>
                      <div className="text-right">
                        <p className="text-violett-900 font-medium">{t.clase_nombre}</p>
                        <Badge variant="outline" className="mt-1">{t.estado}</Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </section>
              </motion.div>
            )}

            {activeTab === 'proximos' && (
              <motion.div key="proximos" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
                <section>
            <h3 className="text-xl font-bold text-foreground mb-4">Próximos Días</h3>
            {data.turnos_semana.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted">
                  No tienes más clases programadas esta semana.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {data.turnos_semana.map((t: any) => (
                  <Card key={t.id}>
                    <CardContent className="flex justify-between items-center p-4">
                      <div>
                        <p className="font-bold text-foreground">{formatFecha(t.fecha)}</p>
                        <p className="text-muted text-sm">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-violett-900 font-medium">{t.clase_nombre}</p>
                        <p className="text-xs text-muted mt-1">{t.cupo_actual} cupos libres</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </section>
              </motion.div>
            )}

            {activeTab === 'recurrentes' && (
              <motion.div key="recurrentes" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }} className="space-y-6">
                <section>
            <h3 className="text-xl font-bold text-foreground mb-4">Mis Clases Recurrentes</h3>
            {data.mis_plantillas && data.mis_plantillas.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted">
                  No tienes horarios fijos semanales asignados.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {data.mis_plantillas?.map((p: any) => (
                  <Card key={p.id}>
                    <CardContent className="flex justify-between items-center p-4">
                      <div>
                        <Badge variant="secondary" className="mb-2">Fija Semanal</Badge>
                        <p className="font-bold text-foreground">Todos los {formatDayOfWeek(p.dia_semana)}s</p>
                        <p className="text-muted text-sm">{p.hora_inicio.slice(0,5)} hs</p>
                      </div>
                      <div className="text-right">
                        <p className="text-violett-900 font-medium">{p.clase_nombre}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </section>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

{/* Right Column: Bolsa de Trabajo */}
        <div className="lg:sticky lg:top-24 flex flex-col h-[calc(100vh-8rem)]">
          <div className="pb-4 mb-4 border-b border-violett-100 shrink-0">
            <h3 className="text-xl font-bold text-violett-900 flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violett-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-violett-500"></span>
              </span>
              Bolsa de Horarios Libres
            </h3>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <section className="space-y-4 pb-8">

            {data.plantillas_libres.length === 0 && data.turnos_libres.length === 0 ? (
              <Card className="bg-violett-50 border-none">
                <CardContent className="py-8 text-center text-muted">
                  No hay clases buscando profesor en este momento.
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                <AnimatePresence mode="popLayout">
                  {data.plantillas_libres.map((p: any) => (
                    <motion.div key={p.id} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}>
                      <Card className="border-violett-200 shadow-sm overflow-hidden relative">
                        <div className="absolute top-0 right-0 bg-violett-100 text-violett-800 text-[10px] font-bold px-2 py-1 rounded-bl-lg uppercase tracking-wider">
                          Fijo Semanal
                        </div>
                        <CardContent className="p-4 pt-6">
                          <p className="font-bold text-foreground">Todos los {formatDayOfWeek(p.dia_semana)}s</p>
                          <p className="text-sm text-muted">{p.hora_inicio.slice(0,5)} hs</p>
                          <div className="mt-3 flex justify-between items-end">
                            <div>
                              <p className="text-violett-700 font-medium">{p.clase_nombre}</p>
                            </div>
                            <Button 
                              size="sm" 
                              onClick={() => setPlantillaToAssign(p.id)}
                              className="bg-blue-600 hover:bg-blue-700 text-white"
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
                              <p className="text-violett-700 font-medium">{t.clase_nombre}</p>
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
              className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" 
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
              className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" 
            />
          </div>
          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-violett-100">
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
  );
}
