import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { toast } from 'sonner';
import { 
  ShieldCheck, 
  Phone, 
  Users, 
  Plus, 
  Trash2, 
  Edit2, 
  Check, 
  X, 
  Bell, 
  BellOff, 
  Sliders, 
  Building, 
  ExternalLink,
  Save,
  Clock,
  Sparkles,
  Info
} from 'lucide-react';

export interface StaffNumber {
  id: string;
  nombre: string;
  telefono: string;
  telefono_original?: string;
  rol: 'DUENA';
  activo: boolean;
  recibe_alertas: boolean;
  notas?: string;
}

export function ConfiguracionAdmin() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'staff' | 'reglas'>('staff');

  // Modal para agregar o editar staff
  const [modalOpen, setModalOpen] = useState(false);
  const [editingStaff, setEditingStaff] = useState<StaffNumber | null>(null);
  const [formNombre, setFormNombre] = useState('');
  const [formTelefono, setFormTelefono] = useState('');
  const [formRecibeAlertas, setFormRecibeAlertas] = useState(true);
  const [formActivo, setFormActivo] = useState(true);
  const [formNotas, setFormNotas] = useState('');

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await api.get('/admin/config/');
      setConfig(res.data);
    } catch (e) {
      toast.error('Error al cargar la configuración');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (updatedConfig?: any) => {
    setSaving(true);
    const cfgToSave = updatedConfig || config;
    try {
      const res = await api.post('/admin/config/', { 
        plugin_config: cfgToSave.plugin_config,
        contact_phone: cfgToSave.contact_phone
      });
      setConfig(res.data);
      toast.success('Configuración guardada correctamente.');
    } catch (e) {
      toast.error('Error al guardar la configuración');
    } finally {
      setSaving(false);
    }
  };

  const getStaffList = (): StaffNumber[] => {
    return config?.plugin_config?.asistente?.staff_telefonos || [];
  };

  const updateStaffList = (newList: StaffNumber[]) => {
    const updated = {
      ...config,
      plugin_config: {
        ...config.plugin_config,
        asistente: {
          ...config.plugin_config?.asistente,
          staff_telefonos: newList
        }
      }
    };
    setConfig(updated);
    handleSave(updated);
  };

  const openAddModal = () => {
    setEditingStaff(null);
    setFormNombre('');
    setFormTelefono('');
    setFormRecibeAlertas(true);
    setFormActivo(true);
    setFormNotas('');
    setModalOpen(true);
  };

  const openEditModal = (staff: StaffNumber) => {
    setEditingStaff(staff);
    setFormNombre(staff.nombre);
    setFormTelefono(staff.telefono_original || staff.telefono);
    setFormRecibeAlertas(staff.recibe_alertas ?? true);
    setFormActivo(staff.activo ?? true);
    setFormNotas(staff.notas || '');
    setModalOpen(true);
  };

  const handleSaveStaffMember = () => {
    if (!formNombre.trim()) {
      toast.error('Por favor ingresá un nombre o referencia para el miembro del staff.');
      return;
    }
    const cleanTel = formTelefono.replace(/[^0-9]/g, '');
    if (cleanTel.length < 8) {
      toast.error('Por favor ingresá un número de teléfono válido (mínimo 8 dígitos).');
      return;
    }

    const currentList = getStaffList();

    if (editingStaff) {
      // Modificar existente
      const updatedList = currentList.map(s => {
        if (s.id === editingStaff.id) {
          return {
            ...s,
            nombre: formNombre.trim(),
            telefono: cleanTel,
            telefono_original: formTelefono.trim(),
            recibe_alertas: formRecibeAlertas,
            activo: formActivo,
            notas: formNotas.trim()
          };
        }
        return s;
      });
      updateStaffList(updatedList);
      toast.success(`Datos de ${formNombre} actualizados.`);
    } else {
      // Agregar nuevo
      const newStaff: StaffNumber = {
        id: `staff_${Date.now()}`,
        nombre: formNombre.trim(),
        telefono: cleanTel,
        telefono_original: formTelefono.trim(),
        rol: 'DUENA',
        activo: formActivo,
        recibe_alertas: formRecibeAlertas,
        notas: formNotas.trim()
      };
      updateStaffList([...currentList, newStaff]);
      toast.success(`${formNombre} agregado al staff del bot de WhatsApp.`);
    }

    setModalOpen(false);
  };

  const handleDeleteStaff = (id: string, nombre: string) => {
    const currentList = getStaffList();
    if (currentList.length <= 1) {
      toast.error('Debe haber al menos un número autorizado en el staff.');
      return;
    }
    if (confirm(`¿Estás seguro de que querés quitar el acceso de dirección a "${nombre}"?`)) {
      const updatedList = currentList.filter(s => s.id !== id);
      updateStaffList(updatedList);
      toast.success(`${nombre} eliminado del staff.`);
    }
  };

  const handleToggleActivo = (id: string) => {
    const currentList = getStaffList();
    const updatedList = currentList.map(s => {
      if (s.id === id) {
        return { ...s, activo: !s.activo };
      }
      return s;
    });
    updateStaffList(updatedList);
  };

  const handleToggleAlertas = (id: string) => {
    const currentList = getStaffList();
    const updatedList = currentList.map(s => {
      if (s.id === id) {
        return { ...s, recibe_alertas: !s.recibe_alertas };
      }
      return s;
    });
    updateStaffList(updatedList);
  };

  const handleReglaChange = (plugin: string, subkey: string, field: string, value: any) => {
    setConfig((prev: any) => {
      const currentPlugin = prev.plugin_config?.[plugin] || {};
      const currentSubkey = currentPlugin[subkey] || {};
      return {
        ...prev,
        plugin_config: {
          ...prev.plugin_config,
          [plugin]: {
            ...currentPlugin,
            [subkey]: {
              ...currentSubkey,
              [field]: value
            }
          }
        }
      };
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-main"></div>
      </div>
    );
  }

  const staffList = getStaffList();
  const coreConfig = config?.plugin_config?.core || {};
  const reglasOperativas = config?.plugin_config?.asistente?.reglas_operativas || {};
  const cancelEmptyConfig = config?.plugin_config?.automatizaciones?.cancel_empty_classes || {};

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-primary-light/50 pb-5">
        <div>
          <h1 className="text-3xl font-bold text-foreground tracking-tight font-serif">Configuración del Negocio</h1>
          <p className="text-sm text-muted mt-1">
            Gestioná los números de staff autorizados para el bot de WhatsApp y las reglas operativas del estudio.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            onClick={() => handleSave()} 
            disabled={saving}
            className="flex items-center gap-2 bg-primary-main text-white shadow-sm hover:bg-primary-hover px-5 py-2.5 rounded-xl font-medium"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Guardando...' : 'Guardar Todo'}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-neutral-200">
        <button
          onClick={() => setActiveTab('staff')}
          className={`flex items-center gap-2.5 py-3 px-5 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'staff'
              ? 'border-primary-main text-primary-main bg-primary-light/30 rounded-t-xl'
              : 'border-transparent text-neutral-500 hover:text-neutral-900'
          }`}
        >
          <ShieldCheck className="w-4 h-4 text-primary-main" />
          <span>Staff y Bot WhatsApp</span>
          <span className="ml-1.5 px-2 py-0.5 rounded-full text-xs bg-primary-main/10 text-primary-main font-bold">
            {staffList.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('reglas')}
          className={`flex items-center gap-2.5 py-3 px-5 text-sm font-semibold border-b-2 transition-all ${
            activeTab === 'reglas'
              ? 'border-primary-main text-primary-main bg-primary-light/30 rounded-t-xl'
              : 'border-transparent text-neutral-500 hover:text-neutral-900'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>Reglas de Negocio y Horarios</span>
        </button>
      </div>

      {/* TAB 1: STAFF Y BOT WHATSAPP */}
      {activeTab === 'staff' && (
        <div className="space-y-6">
          {/* Banner explicativo */}
          <div className="bg-gradient-to-r from-purple-50 via-pink-50/40 to-amber-50/30 border border-purple-200/80 rounded-2xl p-5 shadow-sm">
            <div className="flex items-start gap-3.5">
              <div className="p-2.5 bg-primary-main text-white rounded-xl shadow-sm shrink-0">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-sm font-bold text-primary-main">
                  Acceso Total de Dirección para el Asistente de WhatsApp
                </h3>
                <p className="text-xs text-neutral-600 leading-relaxed">
                  Cualquier número registrado en este listado es reconocido automáticamente por el bot de WhatsApp con permisos de <strong>Dirección (Dueña / Staff)</strong>. Tienen exactamente las mismas opciones que Débora:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 pt-1 text-xs text-neutral-700">
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Mover o reprogramar turnos</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Cancelar o abrir clases</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Ver y corregir asistencias</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Fotos de fichas físicas (Visión)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Ajustar créditos y abonos</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Reportes y métricas contables</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Tarjeta de Lista de Staff */}
          <Card className="border border-neutral-200/90 shadow-sm rounded-2xl overflow-hidden">
            <CardHeader className="bg-neutral-50/70 border-b border-neutral-200/70 py-4 px-6 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold text-foreground flex items-center gap-2">
                  <Users className="w-4 h-4 text-primary-main" />
                  Números Autorizados ({staffList.length})
                </CardTitle>
                <p className="text-xs text-muted mt-0.5">
                  Podés agregar tu nueva línea, números secundarios o personal del estudio encargado de la agenda.
                </p>
              </div>
              <Button 
                onClick={openAddModal}
                className="flex items-center gap-2 bg-primary-main hover:bg-primary-hover text-white text-xs font-semibold px-4 py-2 rounded-xl shadow-sm"
              >
                <Plus className="w-4 h-4" />
                Agregar Número de Staff
              </Button>
            </CardHeader>

            <CardContent className="p-0 divide-y divide-neutral-100">
              {staffList.length === 0 ? (
                <div className="p-8 text-center text-sm text-neutral-500">
                  No hay números registrados. Agregá al menos un número para gestionar el bot.
                </div>
              ) : (
                staffList.map((staff, idx) => {
                  const rawPhone = staff.telefono_original || staff.telefono;
                  const waLink = `https://wa.me/${staff.telefono.replace(/[^0-9]/g, '')}`;

                  return (
                    <div 
                      key={staff.id || idx}
                      className={`p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all hover:bg-neutral-50/60 ${
                        !staff.activo ? 'opacity-60 bg-neutral-50/30' : ''
                      }`}
                    >
                      {/* Avatar y Datos */}
                      <div className="flex items-start sm:items-center gap-3.5">
                        <div className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 shadow-sm ${
                          staff.activo 
                            ? 'bg-primary-light text-primary-main border border-primary-main/20' 
                            : 'bg-neutral-200 text-neutral-500'
                        }`}>
                          {staff.nombre.substring(0, 2).toUpperCase()}
                        </div>

                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className="font-bold text-sm text-neutral-900">{staff.nombre}</h4>
                            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-purple-100 text-purple-800 border border-purple-200">
                              Dirección / Gestión
                            </span>
                            {staff.activo ? (
                              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-100 text-emerald-800 border border-emerald-200">
                                Activo
                              </span>
                            ) : (
                              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-neutral-200 text-neutral-600">
                                Desactivado
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-3 text-xs text-neutral-600 flex-wrap">
                            <a 
                              href={waLink} 
                              target="_blank" 
                              rel="noreferrer"
                              className="flex items-center gap-1 font-mono text-primary-main hover:underline"
                            >
                              <Phone className="w-3.5 h-3.5" />
                              <span>{rawPhone}</span>
                              <ExternalLink className="w-3 h-3 ml-0.5 opacity-60" />
                            </a>

                            <span className="text-neutral-300">•</span>

                            <button
                              onClick={() => handleToggleAlertas(staff.id)}
                              className={`flex items-center gap-1 px-2 py-0.5 rounded-md transition-colors ${
                                staff.recibe_alertas 
                                  ? 'text-amber-700 bg-amber-50 hover:bg-amber-100' 
                                  : 'text-neutral-400 bg-neutral-100 hover:bg-neutral-200'
                              }`}
                              title={staff.recibe_alertas ? 'Recibe avisos por WhatsApp' : 'Alertas desactivadas'}
                            >
                              {staff.recibe_alertas ? <Bell className="w-3 h-3 text-amber-600" /> : <BellOff className="w-3 h-3" />}
                              <span>{staff.recibe_alertas ? 'Recibe Alertas de Clases' : 'Sin Alertas'}</span>
                            </button>
                          </div>

                          {staff.notas && (
                            <p className="text-xs text-neutral-500 italic mt-0.5">{staff.notas}</p>
                          )}
                        </div>
                      </div>

                      {/* Botones de acción */}
                      <div className="flex items-center gap-2 self-end sm:self-center">
                        <button
                          onClick={() => handleToggleActivo(staff.id)}
                          className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
                            staff.activo
                              ? 'border-neutral-200 text-neutral-600 hover:bg-neutral-100'
                              : 'border-emerald-300 text-emerald-700 bg-emerald-50 hover:bg-emerald-100'
                          }`}
                        >
                          {staff.activo ? 'Desactivar' : 'Reactivar'}
                        </button>

                        <button
                          onClick={() => openEditModal(staff)}
                          className="p-2 text-neutral-600 hover:text-primary-main hover:bg-primary-light/50 rounded-lg transition-colors"
                          title="Editar datos"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleDeleteStaff(staff.id, staff.nombre)}
                          className="p-2 text-neutral-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          title="Eliminar del staff"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: REGLAS DE NEGOCIO Y HORARIOS */}
      {activeTab === 'reglas' && (
        <div className="space-y-6">
          <Card className="border border-neutral-200/90 shadow-sm rounded-2xl">
            <CardHeader className="bg-neutral-50/70 border-b border-neutral-200/70 py-4 px-6">
              <CardTitle className="text-base font-bold text-foreground flex items-center gap-2">
                <Clock className="w-4 h-4 text-primary-main" />
                Políticas de Cancelación y Recordatorios
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-semibold text-neutral-900 mb-1">
                  Horas límite de cancelación (Cancelación Tardía)
                </label>
                <p className="text-xs text-neutral-500 mb-2">
                  Si la alumna cancela con menos de esta cantidad de horas de antelación, el sistema considera la cancelación como tardía y descuenta el crédito.
                </p>
                <div className="flex items-center gap-3">
                  <input 
                    type="number" 
                    min="1"
                    max="72"
                    value={coreConfig.horas_limite_cancelacion ?? 2} 
                    onChange={e => handleReglaChange('core', '', 'horas_limite_cancelacion', parseInt(e.target.value) || 2)}
                    className="w-32 p-2.5 text-sm border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-main/20 focus:border-primary-main"
                  />
                  <span className="text-sm font-medium text-neutral-700">horas antes de la clase</span>
                </div>
              </div>

              <div className="border-t border-neutral-100 pt-4">
                <label className="block text-sm font-semibold text-neutral-900 mb-1">
                  Horas de antelación para recordatorios automáticos (Regla 25 hs)
                </label>
                <p className="text-xs text-neutral-500 mb-2">
                  Cantidad de horas previas al inicio de la clase para disparar la notificación de recordatorio.
                </p>
                <div className="flex items-center gap-3">
                  <input 
                    type="number" 
                    min="1"
                    max="72"
                    value={coreConfig.horas_evaluacion_automatica ?? 25} 
                    onChange={e => handleReglaChange('core', '', 'horas_evaluacion_automatica', parseInt(e.target.value) || 25)}
                    className="w-32 p-2.5 text-sm border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-main/20 focus:border-primary-main"
                  />
                  <span className="text-sm font-medium text-neutral-700">horas antes del turno</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border border-neutral-200/90 shadow-sm rounded-2xl">
            <CardHeader className="bg-neutral-50/70 border-b border-neutral-200/70 py-4 px-6">
              <CardTitle className="text-base font-bold text-foreground flex items-center gap-2">
                <Building className="w-4 h-4 text-primary-main" />
                Información del Estudio y Pagos
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-neutral-900 mb-1">Dirección del Estudio</label>
                  <input 
                    type="text" 
                    value={reglasOperativas.direccion || 'Gral. Guido 1573, Ramos Mejía'} 
                    onChange={e => handleReglaChange('asistente', 'reglas_operativas', 'direccion', e.target.value)}
                    className="w-full p-2.5 text-sm border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-main/20"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-neutral-900 mb-1">Alias de Transferencia</label>
                  <input 
                    type="text" 
                    value={reglasOperativas.alias_transferencia || 'VIOLETT.PILATES'} 
                    onChange={e => handleReglaChange('asistente', 'reglas_operativas', 'alias_transferencia', e.target.value)}
                    className="w-full p-2.5 text-sm border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-main/20"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-neutral-900 mb-1">Titular de la Cuenta</label>
                  <input 
                    type="text" 
                    value={reglasOperativas.titular_transferencia || 'Débora Zárate (Deby)'} 
                    onChange={e => handleReglaChange('asistente', 'reglas_operativas', 'titular_transferencia', e.target.value)}
                    className="w-full p-2.5 text-sm border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-main/20"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-neutral-900 mb-1">Cupo Máximo por Camilla / Turno</label>
                  <input 
                    type="number" 
                    min="1"
                    max="10"
                    value={reglasOperativas.max_cupo_por_turno || 3} 
                    onChange={e => handleReglaChange('asistente', 'reglas_operativas', 'max_cupo_por_turno', parseInt(e.target.value) || 3)}
                    className="w-full p-2.5 text-sm border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-main/20"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* MODAL PARA AGREGAR / EDITAR MIEMBRO DEL STAFF */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingStaff ? "Editar Miembro del Staff" : "Agregar Miembro del Staff"}
        subtitle="Asigná un número de WhatsApp para que tenga permisos totales de dirección con el bot."
      >
        <div className="space-y-4 pt-2">
          <div>
            <label className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1">
              Nombre o Referencia *
            </label>
            <input 
              type="text"
              placeholder="ej. Débora (Línea personal) o Valeria (Coordinadora)"
              value={formNombre}
              onChange={e => setFormNombre(e.target.value)}
              className="w-full p-3 text-sm border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-main/20"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1">
              Número de WhatsApp *
            </label>
            <input 
              type="text"
              placeholder="ej. 11 5769-1786 o 5491157691786"
              value={formTelefono}
              onChange={e => setFormTelefono(e.target.value)}
              className="w-full p-3 text-sm font-mono border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-main/20"
            />
            <p className="text-xs text-neutral-500 mt-1.5 flex items-center gap-1">
              <Info className="w-3.5 h-3.5 text-primary-main shrink-0" />
              <span>Podés escribirlo con o sin código de país (+54 9). El bot lo vinculará automáticamente.</span>
            </p>
          </div>

          <div className="space-y-3 pt-2 border-t border-neutral-100">
            <label className="flex items-center gap-3 cursor-pointer">
              <input 
                type="checkbox"
                checked={formRecibeAlertas}
                onChange={e => setFormRecibeAlertas(e.target.checked)}
                className="w-4 h-4 text-primary-main rounded border-neutral-300 focus:ring-primary-main"
              />
              <span className="text-xs text-neutral-700 font-medium">
                Recibir alertas operativas (avisos cuando una clase queda con 1 alumna, cancelaciones y cambios)
              </span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input 
                type="checkbox"
                checked={formActivo}
                onChange={e => setFormActivo(e.target.checked)}
                className="w-4 h-4 text-primary-main rounded border-neutral-300 focus:ring-primary-main"
              />
              <span className="text-xs text-neutral-700 font-medium">
                Número Activo (habilitado para operar con el bot)
              </span>
            </label>
          </div>

          <div>
            <label className="block text-xs font-semibold text-neutral-700 uppercase tracking-wider mb-1">
              Notas adicionales (opcional)
            </label>
            <input 
              type="text"
              placeholder="ej. Encargada de agenda los sábados o celular de soporte"
              value={formNotas}
              onChange={e => setFormNotas(e.target.value)}
              className="w-full p-2.5 text-xs border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-main/20"
            />
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-neutral-100">
            <Button 
              variant="outline"
              onClick={() => setModalOpen(false)}
              className="text-xs px-4 py-2"
            >
              Cancelar
            </Button>
            <Button 
              onClick={handleSaveStaffMember}
              className="bg-primary-main text-white hover:bg-primary-hover text-xs font-semibold px-5 py-2 rounded-xl shadow-sm"
            >
              {editingStaff ? "Guardar Cambios" : "Agregar al Staff"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
