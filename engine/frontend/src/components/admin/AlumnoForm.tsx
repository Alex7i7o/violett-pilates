import { toast } from 'sonner';
import React, { useState } from 'react';
import { Button } from '../ui/Button';

export interface AlumnoFormData {
  nombre: string;
  email: string;
  telefono: string;
  plan_activo: string;
  clases_extra: number;
  fecha_vencimiento_plan: string;
  notas: string;
}

interface AlumnoFormProps {
  initialData?: AlumnoFormData;
  planes: { id: string, nombre: string }[];
  onSubmit: (data: AlumnoFormData) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  submitLabel?: string;
}

export function AlumnoForm({ initialData, planes, onSubmit, onCancel, isSubmitting, submitLabel = 'Guardar' }: AlumnoFormProps) {
  const [formData, setFormData] = useState<AlumnoFormData>(initialData || {
    nombre: '',
    email: '',
    telefono: '',
    plan_activo: '',
    clases_extra: 0,
    fecha_vencimiento_plan: '',
    notas: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: name === 'clases_extra' ? Number(value) : (name === 'email' ? value.toLowerCase() : value) }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form 
      onInvalid={(e) => {
        e.preventDefault();
        const t = typeof toast !== 'undefined' ? toast : (window as any).toast;
        if(t) t.error('Por favor, completa todos los campos requeridos.');
      }}
      onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Nombre</label>
          <input type="text" name="nombre" required value={formData.nombre} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Email</label>
          <input type="email" name="email" required value={formData.email} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Teléfono</label>
          <input type="text" name="telefono" value={formData.telefono} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Plan</label>
          <select name="plan_activo" required value={formData.plan_activo} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light bg-white focus:outline-none focus:ring-2 focus:ring-primary-main">
            <option value="">Seleccione un plan</option>
            {planes.map(p => (
              <option key={p.id} value={p.id}>{p.nombre}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Clases Extra</label>
          <input type="number" name="clases_extra" min="0" value={formData.clases_extra} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Vencimiento Plan</label>
          <input type="date" name="fecha_vencimiento_plan" value={formData.fecha_vencimiento_plan} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" />
        </div>
      </div>
      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Notas Internas</label>
        <textarea name="notas" rows={3} value={formData.notas} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main"></textarea>
      </div>
      <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-primary-light">
        <Button type="button" variant="outline" onClick={onCancel}>Cancelar</Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Guardando...' : submitLabel}
        </Button>
      </div>
    </form>
  );
}
