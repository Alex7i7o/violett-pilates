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

  if (loading) return <p className="text-muted p-4">Cargando panel...</p>;
  if (!data) return <p className="text-muted p-4">Error cargando el panel.</p>;

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
            <h3 className="text-xl font-bold text-foreground mb-4">Clases de Hoy</h3>
            {data.turnos_hoy.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted">
                  No tienes clases asignadas para hoy.
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {data.turnos_hoy.map((t: any) => (
                  <Card key={t.id} className="border-l-4 border-l-violett-600">
                    <CardContent className="flex justify-between items-center p-4">
                      <div>
                        <p className="font-bold text-foreground text-lg">{t.hora_inicio.slice(0,5)} - {t.hora_fin.slice(0,5)}</p>
                        <p className="text-violett-900 font-medium">{t.clase_nombre}</p>
                      </div>
                      <Badge variant="default" className="bg-violett-100 text-violett-900 border-none">
                        {t.cupo_actual} cupos libres
                      </Badge>
                    </CardContent>
                  </Card>
                ))}
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
            <h3 className="text-xl font-bold text-foreground mb-4">Bolsa de Clases</h3>
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
