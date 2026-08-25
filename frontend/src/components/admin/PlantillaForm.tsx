import React, { useState } from 'react';
import { Button } from '../ui/Button';

export interface PlantillaFormData {
  dia_semana: string;
  hora_inicio: string;
  hora_fin: string;
  clase_nombre: string;
  profesor_id: string;
}

interface PlantillaFormProps {
  initialData?: PlantillaFormData;
  profesores: any[];
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

export function PlantillaForm({ initialData, profesores, onSubmit, onCancel, isSubmitting }: PlantillaFormProps) {
  const [formData, setFormData] = useState<PlantillaFormData>(initialData || {
    dia_semana: '1',
    hora_inicio: '09:00',
    hora_fin: '10:00',
    clase_nombre: 'Mat Pilates',
    profesor_id: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Día de la semana</label>
        <select name="dia_semana" value={formData.dia_semana} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white">
          {DIAS.map(d => (
            <option key={d.val} value={d.val}>{d.label}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Hora de inicio</label>
          <input type="time" name="hora_inicio" required value={formData.hora_inicio} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Hora de fin</label>
          <input type="time" name="hora_fin" required value={formData.hora_fin} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
        </div>
      </div>

      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Tipo de Clase</label>
        <input type="text" name="clase_nombre" required value={formData.clase_nombre} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
      </div>

      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Profesor Asignado</label>
        <select name="profesor_id" value={formData.profesor_id} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white">
          <option value="">Dejar libre (Bolsa de trabajo)</option>
          {profesores.map(p => (
            <option key={p.id} value={p.id}>{p.nombre} {p.apellido}</option>
          ))}
        </select>
      </div>

      <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-violett-100">
        <Button type="button" variant="outline" onClick={onCancel}>Cancelar</Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Guardando...' : 'Guardar Horario'}
        </Button>
      </div>
    </form>
  );
}
