import { toast } from 'sonner';
import React, { useState, useEffect } from 'react';
import { Button } from '../ui/Button';
import { MultiSelectAlumnos } from './MultiSelectAlumnos';

export interface AlumnoManual {
  id?: string;
  nombre_temporal: string;
  telefono_temporal?: string;
}

export interface PlantillaFormData {
  dia_semana: string;
  hora_inicio: string;
  hora_fin: string;
  clase: string;
  profesor: string;
  alumnos: string[];
  alumnos_manuales?: AlumnoManual[];
}

interface PlantillaFormProps {
  initialData?: PlantillaFormData;
  profesores: any[];
  clases: any[];
  onSubmit: (data: PlantillaFormData) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}

const DIAS = [
  { val: '1', label: 'Lunes' },
  { val: '2', label: 'Martes' },
  { val: '3', label: 'Miércoles' },
  { val: '4', label: 'Jueves' },
  { val: '5', label: 'Viernes' },
  { val: '6', label: 'Sábado' },
  { val: '7', label: 'Domingo' }
];

export function PlantillaForm({ initialData, profesores, clases, onSubmit, onCancel, isSubmitting }: PlantillaFormProps) {
  const [formData, setFormData] = useState<PlantillaFormData>(initialData || {
    dia_semana: '1',
    hora_inicio: '09:00',
    hora_fin: '10:00',
    clase: '',
    profesor: '',
    alumnos: [],
    alumnos_manuales: []
  });

  const [alumnosManuales, setAlumnosManuales] = useState<AlumnoManual[]>(initialData?.alumnos_manuales || []);
  const [nuevoNombreManual, setNuevoNombreManual] = useState('');
  const [nuevoTelefonoManual, setNuevoTelefonoManual] = useState('');

  const selectedClase = clases.find((c: any) => c.id.toString() === formData.clase.toString());
  const cupoMaximo = selectedClase?.cupo_maximo || 3;
  const totalOcupadas = (formData.alumnos?.length || 0) + alumnosManuales.length;

  useEffect(() => {
    if (formData.hora_inicio) {
      const duration = (selectedClase && selectedClase.duracion_minutos) ? selectedClase.duracion_minutos : 60;
      
      const [hours, minutes] = formData.hora_inicio.split(':').map(Number);
      const totalMinutes = hours * 60 + minutes + duration;
      const endHours = Math.floor(totalMinutes / 60) % 24;
      const endMinutes = totalMinutes % 60;
      const newHoraFin = `${String(endHours).padStart(2, '0')}:${String(endMinutes).padStart(2, '0')}`;
      
      setFormData(prev => {
        if (prev.hora_fin !== newHoraFin) {
          return { ...prev, hora_fin: newHoraFin };
        }
        return prev;
      });
    }
  }, [formData.hora_inicio, formData.clase, clases, selectedClase]);

  const handleAddManual = (e: React.MouseEvent) => {
    e.preventDefault();
    const nombre = nuevoNombreManual.trim();
    if (!nombre) {
      toast.error('Ingresa el nombre de la clienta para apartar la camilla');
      return;
    }
    if (totalOcupadas >= cupoMaximo) {
      toast.warning(`Atención: la clase ya tiene ${totalOcupadas}/${cupoMaximo} camillas asignadas.`);
    }

    const updated = [
      ...alumnosManuales,
      {
        nombre_temporal: nombre,
        telefono_temporal: nuevoTelefonoManual.trim()
      }
    ];
    setAlumnosManuales(updated);
    setFormData(prev => ({ ...prev, alumnos_manuales: updated }));
    setNuevoNombreManual('');
    setNuevoTelefonoManual('');
    toast.success(`Camilla apartada para ${nombre}`);
  };

  const handleRemoveManual = (indexToRemove: number) => {
    const updated = alumnosManuales.filter((_, idx) => idx !== indexToRemove);
    setAlumnosManuales(updated);
    setFormData(prev => ({ ...prev, alumnos_manuales: updated }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      alumnos_manuales: alumnosManuales
    });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <form 
      onInvalid={(e) => {
        e.preventDefault();
        toast.error('Por favor, completa todos los campos requeridos.');
      }}
      onSubmit={handleSubmit} 
      className="space-y-4 text-left"
    >
      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Día de la semana</label>
        <select name="dia_semana" value={formData.dia_semana} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary-main bg-white">
          {DIAS.map(d => (
            <option key={d.val} value={d.val}>{d.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Clase</label>
        <select name="clase" required value={formData.clase} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary-main bg-white">
          <option value="">Selecciona una clase</option>
          {clases.map(c => (
            <option key={c.id} value={c.id}>{c.nombre} (Capacidad: {c.cupo_maximo || 3} camillas)</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Hora de inicio</label>
          <input type="time" name="hora_inicio" required value={formData.hora_inicio} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary-main" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Hora de fin</label>
          <input type="time" name="hora_fin" required value={formData.hora_fin} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary-main" />
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Profesor Asignado</label>
        <select name="profesor" value={formData.profesor} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary-main bg-white">
          <option value="">Dejar libre (Bolsa de trabajo)</option>
          {profesores.map(p => (
            <option key={p.id} value={p.id}>{p.nombre} {p.apellido}</option>
          ))}
        </select>
      </div>

      {/* Indicador de ocupación de camillas */}
      <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs">
        <span className="font-semibold text-slate-700">Estado de Camillas en este horario:</span>
        <span className={`px-2.5 py-1 rounded-lg font-bold ${totalOcupadas > cupoMaximo ? 'bg-rose-100 text-rose-700' : totalOcupadas === cupoMaximo ? 'bg-emerald-100 text-emerald-800' : 'bg-primary-light/50 text-primary-main'}`}>
          {totalOcupadas} / {cupoMaximo} camillas ocupadas
        </span>
      </div>

      {/* Sección 1: Alumnas Registradas con Cuenta */}
      <div className="pt-2 border-t border-slate-100">
        <label className="block text-sm font-semibold mb-1 text-foreground">
          Alumnas Registradas en la Web (Recurrentes)
        </label>
        <MultiSelectAlumnos 
          selectedIds={formData.alumnos} 
          onChange={(ids) => setFormData(prev => ({...prev, alumnos: ids}))} 
        />
      </div>

      {/* Sección 2: Camillas Apartadas Manualmente (Sin cuenta web) */}
      <div className="pt-3 border-t border-slate-100">
        <div className="flex items-center justify-between mb-1.5">
          <label className="block text-sm font-semibold text-foreground">
            Camillas Apartadas Manualmente <span className="text-xs font-normal text-muted">(Sin cuenta web)</span>
          </label>
          <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">
            ✦ Horario Fijo
          </span>
        </div>
        <p className="text-xs text-muted mb-2.5 leading-relaxed">
          Para clientas habituales que aún no se registraron en la app. La camilla quedará apartada todas las semanas a su nombre y nadie podrá ocuparla por la web ni por WhatsApp.
        </p>

        {/* Formulario rápido para agregar clienta manual */}
        <div className="flex flex-col sm:flex-row gap-2 mb-3">
          <input 
            type="text" 
            placeholder="Nombre y apellido (ej: Marcela Pérez)"
            value={nuevoNombreManual}
            onChange={(e) => setNuevoNombreManual(e.target.value)}
            className="flex-1 p-2.5 sm:p-2 rounded-xl border border-primary-light text-base sm:text-xs focus:outline-none focus:ring-2 focus:ring-primary-main bg-white"
          />
          <input 
            type="text" 
            placeholder="Teléfono (opcional)"
            value={nuevoTelefonoManual}
            onChange={(e) => setNuevoTelefonoManual(e.target.value)}
            className="sm:w-36 p-2.5 sm:p-2 rounded-xl border border-primary-light text-base sm:text-xs focus:outline-none focus:ring-2 focus:ring-primary-main bg-white"
          />
          <Button 
            type="button" 
            onClick={handleAddManual}
            variant="outline"
            className="shrink-0 text-xs py-2 h-auto border-primary-main text-primary-main hover:bg-primary-light/30"
          >
            + Apartar Camilla
          </Button>
        </div>

        {/* Lista de camillas apartadas */}
        {alumnosManuales.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {alumnosManuales.map((m, idx) => (
              <div 
                key={idx} 
                className="flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-900 px-3 py-1.5 rounded-xl text-xs font-medium shadow-sm"
              >
                <span>🏷️ {m.nombre_temporal}</span>
                {m.telefono_temporal && (
                  <span className="text-[10px] text-amber-700/80 font-mono">({m.telefono_temporal})</span>
                )}
                <button
                  type="button"
                  onClick={() => handleRemoveManual(idx)}
                  className="text-amber-700 hover:text-red-600 hover:bg-amber-100 h-4 w-4 rounded-full flex items-center justify-center font-bold text-sm ml-1 transition-colors"
                  title="Quitar apartado manual"
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted/70 italic">No hay camillas apartadas manualmente para este horario.</p>
        )}
      </div>

      <div className="sticky bottom-0 bg-white/95 backdrop-blur-sm -mx-4 -mb-4 p-4 sm:-mx-6 sm:-mb-6 sm:p-5 border-t border-primary-light flex items-center justify-end gap-3 z-10 mt-6 shadow-[0_-4px_12px_rgba(0,0,0,0.03)]">
        <Button type="button" variant="outline" onClick={onCancel}>Cancelar</Button>
        <Button type="submit" disabled={isSubmitting} className="min-w-[130px]">
          {isSubmitting ? 'Guardando...' : 'Guardar Horario'}
        </Button>
      </div>
    </form>
  );
}
