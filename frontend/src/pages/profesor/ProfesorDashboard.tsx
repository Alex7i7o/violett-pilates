import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';

import { Modal } from '../../components/ui/Modal';

export function ProfesorDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Password change state
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [changingPwd, setChangingPwd] = useState(false);
  const [bolsaTab, setBolsaTab] = useState<'SUELTOS' | 'FIJOS'>('SUELTOS');

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.get('/profesor/dashboard/');
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleAssign = async (turnoId: string) => {
    if (!confirm('¿Estás seguro de que quieres dar esta clase?')) return;
    try {
      await api.post(`/profesor/turnos/${turnoId}/assign/`);
      alert('¡Clase asignada exitosamente!');
      fetchDashboard();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error asignando la clase');
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setChangingPwd(true);
    try {
      await api.post('/auth/password/change/', {
        old_password: oldPassword,
        new_password1: newPassword,
        new_password2: newPassword
      });
      alert('Contraseña actualizada exitosamente');
      setShowPasswordModal(false);
      setOldPassword('');
      setNewPassword('');
    } catch (e: any) {
      alert('Error cambiando contraseña. Revisa que la clave actual sea correcta.');
    } finally {
      setChangingPwd(false);
    }
  };

  const [showPast, setShowPast] = useState(false);

  if (loading) return <p className="text-muted p-4">Cargando panel...</p>;
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
          <h2 className="text-3xl font-bold text-violett-900">Hola, Profesor</h2>
          <div className="flex items-center gap-3 mt-1">
            <p className="text-muted">Este es tu resumen de clases</p>
            <Button variant="outline" size="sm" onClick={() => setShowPasswordModal(true)}>
              Cambiar Contraseña
            </Button>
          </div>
        </div>
        
        <div className="bg-violett-50 border border-violett-100 px-6 py-4 rounded-2xl flex items-center gap-4">
          <div className="w-12 h-12 bg-violett-900 rounded-full flex items-center justify-center text-white text-xl font-bold">
            {data.horas_mes}
          </div>
          <div>
            <p className="text-sm font-bold text-violett-900 uppercase tracking-wider">Clases Dictadas</p>
            <p className="text-xs text-violett-600">En este mes</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Agenda (Hoy y Semana) */}
        <div className="lg:col-span-2 space-y-8">
          
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
                  No tienes m�s clases para hoy.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                <AnimatePresence>
                  {displayHoy.map((t: any) => {
                    const isPast = t.hora_fin.slice(0,5) < currentHHMM;
                    return (
                      <motion.div key={t.id} initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                        <Card className={order-l-4 \}>
                          <CardContent className="flex justify-between items-center p-4">
                            <div>
                              <p className="font-bold text-foreground text-lg">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)}</p>
                              <p className="\ font-medium">{t.clase_nombre}</p>
                            </div>
                            <Badge variant="default" className="\ border-none">
                              {isPast ? 'Dada' : \ cupos libres}
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

          <section>
            <h3 className="text-xl font-bold text-foreground mb-4">Próximos Días</h3>
            {data.turnos_semana.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted">
                  No tienes más clases esta semana.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {data.turnos_semana.map((t: any) => (
                  <Card key={t.id}>
                    <CardContent className="flex justify-between items-center p-4">
                      <div>
                        <p className="font-bold text-foreground">{t.fecha} | {t.hora_inicio.slice(0,5)}</p>
                        <p className="text-muted text-sm">{t.clase_nombre}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </section>

        </div>

        {/* Right Column: Bolsa de Trabajo */}
        <div>
          <section>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-foreground">Bolsa de Trabajo</h3>
            </div>
            
            <div className="flex gap-2 mb-4 bg-violett-50 p-1 rounded-xl border border-violett-100">
              <button 
                className={`flex-1 py-1.5 text-sm font-semibold rounded-lg transition-colors ${bolsaTab === 'SUELTOS' ? 'bg-white shadow-sm text-violett-900' : 'text-muted hover:text-foreground'}`}
                onClick={() => setBolsaTab('SUELTOS')}
              >
                Sueltos
              </button>
              <button 
                className={`flex-1 py-1.5 text-sm font-semibold rounded-lg transition-colors ${bolsaTab === 'FIJOS' ? 'bg-white shadow-sm text-violett-900' : 'text-muted hover:text-foreground'}`}
                onClick={() => setBolsaTab('FIJOS')}
              >
                Fijos
              </button>
            </div>

            {bolsaTab === 'SUELTOS' ? (
              <AnimatePresence mode="wait">
                <motion.div key="sueltos" initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }}>
                  <p className="text-sm text-muted mb-4">Clases sin profesor asignado. Puedes tomarlas si tienes disponibilidad.</p>
                  
                  {data.turnos_libres.length === 0 ? (
                    <Card>
                      <CardContent className="py-8 text-center text-muted text-sm">
                        No hay clases libres en este momento.
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="grid gap-3">
                      {data.turnos_libres.map((t: any) => (
                        <Card key={t.id} className="bg-emerald-50/50 border-emerald-100 hover:shadow-sm transition-all">
                          <CardContent className="p-4 flex flex-col gap-3">
                            <div>
                              <p className="font-bold text-emerald-900">{t.fecha} | {t.hora_inicio.slice(0,5)}</p>
                              <p className="text-emerald-700 text-sm font-medium">{t.clase_nombre}</p>
                            </div>
                            <Button 
                              size="sm" 
                              onClick={() => handleAssign(t.id)}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white w-full"
                            >
                              Dar esta clase
                            </Button>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            ) : (
              <AnimatePresence mode="wait">
                <motion.div key="fijos" initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }}>
                  <p className="text-sm text-muted mb-4">Horarios fijos semanales sin profesor asignado. Puedes tomarlos de forma permanente.</p>
                  
                  {data.plantillas_libres?.length === 0 ? (
                    <Card>
                      <CardContent className="py-8 text-center text-muted text-sm">
                        No hay horarios fijos libres.
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="grid gap-3">
                      {data.plantillas_libres?.map((p: any) => {
                        const dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
                        return (
                          <Card key={p.id} className="bg-blue-50/50 border-blue-100 hover:shadow-sm transition-all">
                            <CardContent className="p-4 flex flex-col gap-3">
                              <div>
                                <p className="font-bold text-blue-900">Todos los {dias[p.dia_semana-1]} | {p.hora_inicio.slice(0,5)}</p>
                                <p className="text-blue-700 text-sm font-medium">{p.clase_nombre}</p>
                              </div>
                              <Button 
                                size="sm" 
                                onClick={() => handleAssignPlantilla(p.id)}
                                className="bg-blue-600 hover:bg-blue-700 text-white w-full"
                              >
                                Tomar horario fijo
                              </Button>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            )}
          </section>
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

    </motion.div>
  );
}

