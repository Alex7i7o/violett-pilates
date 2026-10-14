import React, { useState, useEffect } from 'react';
import { useClientProfile } from '../../hooks/useClientProfile';
import { ClientProfileHeader } from '../../components/dashboard/ClientProfileHeader';
import { api } from '../../lib/api';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { LogOut, Bell, BellRing, Save, AlertCircle, CheckCircle2, User } from 'lucide-react';
import { usePushNotifications } from '../../hooks/usePushNotifications';
import { useClientConfig } from '../../context/ClientConfigContext';
import { toast } from 'sonner';

export function PerfilView() {
  const { profile, refetch } = useClientProfile();
  const config = useClientConfig();
  const { isSupported, isSubscribed, subscribe, reactivate, testPush } = usePushNotifications();

  // Form State
  const [nombre, setNombre] = useState('');
  const [apellido, setApellido] = useState('');
  const [telefono, setTelefono] = useState('');
  const [fechaNacimiento, setFechaNacimiento] = useState('');
  const [sexo, setSexo] = useState('');
  const [contactoEmergencia, setContactoEmergencia] = useState('');
  const [notasMedicas, setNotasMedicas] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (profile) {
      setNombre(profile.nombre || profile.name?.split(' ')[0] || '');
      setApellido(profile.apellido || (profile.name ? profile.name.split(' ').slice(1).join(' ') : ''));
      setTelefono(profile.telefono || '');
      setFechaNacimiento(profile.fecha_nacimiento || '');
      setSexo(profile.sexo || '');
      setContactoEmergencia(profile.contacto_emergencia || '');
      setNotasMedicas(profile.notas_medicas || '');
    }
  }, [profile]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombre.trim()) {
      toast.error('Por favor ingresá tu nombre.');
      return;
    }
    setSaving(true);
    try {
      await api.patch('/profile/', {
        nombre: nombre.trim(),
        apellido: apellido.trim(),
        telefono: telefono.trim(),
        fecha_nacimiento: fechaNacimiento || null,
        sexo: sexo || '',
        contacto_emergencia: contactoEmergencia.trim(),
        notas_medicas: notasMedicas.trim(),
      });
      toast.success('¡Tus datos fueron actualizados correctamente!');
      await refetch();
    } catch (err: any) {
      console.error(err);
      toast.error('Ocurrió un error al guardar los datos.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    const baseUrl = import.meta.env.BASE_URL || '/';
    const loginPath = baseUrl.endsWith('/') ? baseUrl + 'login' : baseUrl + '/login';
    try {
      await api.post('/auth/logout/');
    } catch (e) {
      // ignore
    } finally {
      document.body.innerHTML = '';
      window.location.replace(loginPath);
    }
  };

  const handleTestPush = async () => {
    try {
      const res = await api.get('/webpush/test/');
      console.log('[Push] Test response:', res.data);
      toast.success('Notificacion enviada. Deberia aparecer en unos segundos.');
    } catch (e: any) {
      const detail = e.response?.data?.detail || e.message || 'Error desconocido';
      console.error('[Push] Test error:', detail);
      toast.error(`Error enviando notificacion: ${detail}`);
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 md:px-0 pt-4 md:pt-0 pb-6 space-y-8">
      <div className="md:hidden mt-2 mb-2">
        <h1 className="text-3xl font-bold text-foreground">Mi Perfil</h1>
      </div>

      {profile && (
        <ClientProfileHeader 
          profile={profile} 
          onPlanUpdate={refetch}
        />
      )}

      {/* Formulario de Datos Personales y Ficha Médica */}
      <Card className="shadow-glass bg-white border border-primary-light/60">
        <CardHeader className="pb-4 border-b border-primary-light/30">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-primary-light/40 flex items-center justify-center text-primary-main">
              <User className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-foreground">Mis Datos Personales y Ficha</CardTitle>
              <p className="text-xs text-muted mt-0.5">Mantené tu información y ficha médica al día para una mejor experiencia</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {profile?.perfil_incompleto ? (
            <div className="bg-amber-50/90 border border-amber-200/90 rounded-2xl p-4 mb-6 flex items-start gap-3 shadow-sm">
              <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="text-xs sm:text-sm text-amber-950">
                <p className="font-bold">Tenés datos pendientes por completar en tu ficha</p>
                <p className="mt-0.5 text-amber-900/80 leading-relaxed">
                  Completá los campos indicados como <span className="font-semibold text-amber-800 bg-amber-100/80 px-1.5 py-0.5 rounded text-[11px]">Pendiente</span> (fecha de nacimiento, sexo y contacto de emergencia) para finalizar tu perfil.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-emerald-50/80 border border-emerald-200/80 rounded-2xl p-3.5 mb-6 flex items-center gap-2.5 shadow-sm">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <p className="text-xs sm:text-sm font-medium text-emerald-950">
                ¡Tu perfil y ficha médica están completos!
              </p>
            </div>
          )}

          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs sm:text-sm font-semibold mb-1 text-foreground">
                  Nombre <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={nombre}
                  onChange={e => setNombre(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main text-sm"
                />
              </div>

              <div>
                <label className="block text-xs sm:text-sm font-semibold mb-1 text-foreground">
                  Apellido
                </label>
                <input
                  type="text"
                  value={apellido}
                  onChange={e => setApellido(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main text-sm"
                />
              </div>

              <div>
                <label className="block text-xs sm:text-sm font-semibold mb-1 text-foreground">
                  Email
                </label>
                <input
                  type="email"
                  disabled
                  value={profile?.email || ''}
                  className="w-full p-2.5 rounded-xl border border-gray-200 bg-gray-50/80 text-gray-500 cursor-not-allowed text-sm"
                />
                <p className="text-[10px] text-muted-foreground mt-1">El email no se puede modificar directamente.</p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs sm:text-sm font-semibold text-foreground">
                    Teléfono (WhatsApp) <span className="text-red-500">*</span>
                  </label>
                  {!telefono && (
                    <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-md">
                      Pendiente
                    </span>
                  )}
                </div>
                <input
                  type="text"
                  required
                  value={telefono}
                  onChange={e => setTelefono(e.target.value)}
                  placeholder="Ej: 11 5555-5555"
                  className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main text-sm"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs sm:text-sm font-semibold text-foreground">
                    Fecha de Nacimiento
                  </label>
                  {!fechaNacimiento ? (
                    <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-md">
                      Pendiente
                    </span>
                  ) : profile?.edad !== null && profile?.edad !== undefined ? (
                    <span className="text-[11px] font-semibold text-primary-main">
                      {profile.edad} años
                    </span>
                  ) : null}
                </div>
                <input
                  type="date"
                  value={fechaNacimiento}
                  onChange={e => setFechaNacimiento(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-primary-light bg-white focus:outline-none focus:ring-2 focus:ring-primary-main text-sm"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs sm:text-sm font-semibold text-foreground">
                    Sexo
                  </label>
                  {!sexo && (
                    <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-md">
                      Pendiente
                    </span>
                  )}
                </div>
                <select
                  value={sexo}
                  onChange={e => setSexo(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-primary-light bg-white focus:outline-none focus:ring-2 focus:ring-primary-main text-sm"
                >
                  <option value="">Seleccionar...</option>
                  <option value="F">Femenino</option>
                  <option value="M">Masculino</option>
                  <option value="O">Otro</option>
                  <option value="N">Prefiero no decirlo</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs sm:text-sm font-semibold text-foreground">
                    Contacto de Emergencia
                  </label>
                  {!contactoEmergencia && (
                    <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-md">
                      Pendiente
                    </span>
                  )}
                </div>
                <input
                  type="text"
                  maxLength={100}
                  value={contactoEmergencia}
                  onChange={e => setContactoEmergencia(e.target.value)}
                  placeholder="Ej: Mamá - 11 4444-4444"
                  className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main text-sm"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs sm:text-sm font-semibold mb-1 text-foreground">
                  Notas Médicas, Cirugías o Lesiones
                </label>
                <textarea
                  rows={3}
                  value={notasMedicas}
                  onChange={e => setNotasMedicas(e.target.value)}
                  placeholder="Contanos si tenés alguna lesión, molestia articular o indicación médica para que tu instructora la tenga en cuenta..."
                  className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main text-sm"
                />
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <Button
                type="submit"
                disabled={saving}
                className="w-full sm:w-auto px-6 py-2.5 bg-primary-main hover:bg-primary-hover text-white font-bold rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Guardando...' : 'Guardar mis datos'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Acciones de Perfil */}
      <div className="pt-6 border-t border-primary-light/40 space-y-3">
        {config.features?.webpush && isSupported && !isSubscribed && (
          <Button 
            variant="outline" 
            onClick={subscribe}
            className="w-full text-primary-main border-primary-light hover:bg-primary-light/20"
          >
            <Bell className="w-5 h-5 mr-2" />
            Activar Avisos de Turnos Libres
          </Button>
        )}

        {config.features?.webpush && isSupported && isSubscribed && (
          <Button 
            variant="outline" 
            onClick={handleTestPush}
            className="w-full text-green-700 border-green-200 hover:bg-green-50"
          >
            <BellRing className="w-5 h-5 mr-2" />
            Probar Notificaciones
          </Button>
        )}

        <Button 
          variant="outline" 
          onClick={handleLogout}
          className="w-full text-red-600 border-red-200 hover:bg-red-50"
        >
          <LogOut className="w-5 h-5 mr-2" />
          Cerrar Sesion
        </Button>
      </div>
    </div>
  );
}
