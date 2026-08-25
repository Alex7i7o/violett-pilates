import React, { useState } from 'react';
import { Button } from '../ui/Button';

export interface ProfesorFormData {
  nombre: string;
  email: string;
  telefono: string;
  color: string;
}

interface ProfesorFormProps {
  initialData?: ProfesorFormData;
  onSubmit: (data: ProfesorFormData) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
  submitLabel?: string;
}

export function ProfesorForm({ initialData, onSubmit, onCancel, isSubmitting, submitLabel = 'Guardar' }: ProfesorFormProps) {
  const [formData, setFormData] = useState<ProfesorFormData>(initialData || {
    nombre: '',
    email: '',
    telefono: '',
    color: '#6d28d9'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Nombre</label>
          <input type="text" name="nombre" required value={formData.nombre} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Email</label>
          <input type="email" name="email" required value={formData.email} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Teléfono</label>
          <input type="text" name="telefono" value={formData.telefono} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
        </div>
        <div>
          <label className="block text-sm font-semibold mb-1 text-foreground">Color</label>
          <input type="color" name="color" value={formData.color} onChange={handleChange} className="w-full h-11 px-1 py-1 rounded-xl cursor-pointer border border-violett-200" />
        </div>
      </div>
      <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-violett-100">
        <Button type="button" variant="outline" onClick={onCancel}>Cancelar</Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Guardando...' : submitLabel}
        </Button>
      </div>
    </form>
  );
}
