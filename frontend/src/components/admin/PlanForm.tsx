import React, { useState, useEffect } from 'react';
import { Button } from '../ui/Button';

export interface PlanFormData {
  nombre: string;
  clases_por_mes: number;
  precio: number;
}

interface PlanFormProps {
  initialData?: PlanFormData | null;
  onSubmit: (data: PlanFormData) => Promise<void>;
  onCancel: () => void;
  isEditing: boolean;
}

export function PlanForm({ initialData, onSubmit, onCancel, isEditing }: PlanFormProps) {
  const [formData, setFormData] = useState<PlanFormData>({
    nombre: '',
    clases_por_mes: 0,
    precio: 0
  });

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      setFormData({ nombre: '', clases_por_mes: 0, precio: 0 });
    }
  }, [initialData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: name === 'nombre' ? value : Number(value) }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="col-span-1 md:col-span-2">
        <label className="block text-sm font-semibold mb-1 text-foreground">Nombre</label>
        <input type="text" name="nombre" required value={formData.nombre} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
      </div>
      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Clases al Mes</label>
        <input type="number" name="clases_por_mes" required min="1" value={formData.clases_por_mes} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
      </div>
      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Precio ($)</label>
        <input type="number" name="precio" required min="0" step="0.01" value={formData.precio} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
      </div>
      <div className="col-span-1 md:col-span-4 flex justify-end gap-3 mt-2">
        {isEditing && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
        )}
        <Button type="submit">
          {isEditing ? 'Guardar Cambios' : 'Crear Plan'}
        </Button>
      </div>
    </form>
  );
}
