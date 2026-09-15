import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { toast } from 'sonner';

export function ReglasNegocioAdmin() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await api.get('/admin/config/');
      setConfig(res.data);
    } catch (e) {
      toast.error('Error al cargar configuración');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.post('/admin/config/', { plugin_config: config.plugin_config });
      toast.success('Reglas actualizadas. Los cambios aplicarán en las próximas ejecuciones.');
    } catch (e) {
      toast.error('Error al guardar configuración');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (plugin: string, key: string, value: any) => {
    setConfig((prev: any) => ({
      ...prev,
      plugin_config: {
        ...prev.plugin_config,
        [plugin]: {
          ...prev.plugin_config[plugin],
          [key]: value
        }
      }
    }));
  };

  if (loading) return <div className="p-4">Cargando reglas de negocio...</div>;
  if (!config) return <div className="p-4">No se encontró la configuración.</div>;

  const coreConfig = config.plugin_config?.core || {};
  const cancelEmptyConfig = config.plugin_config?.automatizaciones?.cancel_empty_classes || {};

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-foreground">Reglas del Negocio</h1>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Guardando...' : 'Guardar Cambios'}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Reservas y Cancelaciones</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Horas límite de cancelación (Cancelación Tardía)</label>
            <p className="text-xs text-muted mb-2">Si el alumno cancela con menos de estas horas de anticipación, pierde la clase.</p>
            <input 
              type="number" 
              value={coreConfig.horas_limite_cancelacion || 12} 
              onChange={e => handleChange('core', 'horas_limite_cancelacion', parseInt(e.target.value))}
              className="w-full max-w-sm p-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Horas de antelación para notificaciones (ej. Regla 25hs)</label>
            <p className="text-xs text-muted mb-2">Se enviará el recordatorio a esta cantidad de horas antes de la clase.</p>
            <input 
              type="number" 
              value={coreConfig.horas_evaluacion_automatica || 25} 
              onChange={e => handleChange('core', 'horas_evaluacion_automatica', parseInt(e.target.value))}
              className="w-full max-w-sm p-2 border rounded-lg"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Automatizaciones de Clases Vacías</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Horas antes de la clase para evaluar cupo mínimo</label>
            <input 
              type="number" 
              value={cancelEmptyConfig.hours_before_class || 24} 
              onChange={e => handleChange('automatizaciones', 'cancel_empty_classes', { ...cancelEmptyConfig, hours_before_class: parseInt(e.target.value) } as any)}
              className="w-full max-w-sm p-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Cupo mínimo para dictar la clase</label>
            <input 
              type="number" 
              value={cancelEmptyConfig.min_students || 2} 
              onChange={e => handleChange('automatizaciones', 'cancel_empty_classes', { ...cancelEmptyConfig, min_students: parseInt(e.target.value) } as any)}
              className="w-full max-w-sm p-2 border rounded-lg"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}