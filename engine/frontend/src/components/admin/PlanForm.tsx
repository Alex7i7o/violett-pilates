import { toast } from 'sonner';
﻿import React, { useState, useEffect } from 'react';
import { Button } from '../ui/Button';

export interface PlanFormData {
  nombre: string;
  clases_por_mes: number | '';
  precio: string;
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
    clases_por_mes: '',
    precio: ''
  });

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      setFormData({ nombre: '', clases_por_mes: '', precio: '' });
    }
  }, [initialData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    if (name === 'precio') {
        const rawValue = value.replace(/\./g, '');
        if (/^\d*$/.test(rawValue)) {
            const formatted = rawValue ? Number(rawValue).toLocaleString('es-AR') : '';
            setFormData(prev => ({ ...prev, [name]: formatted }));
        }
        return;
    }
    setFormData(prev => ({ 
      ...prev, 
      [name]: name === 'nombre' ? value : (value === '' ? '' : Number(value)) 
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const finalData = {
        ...formData,
        precio: Number(String(formData.precio).replace(/\./g, ''))
    };
    onSubmit(finalData as any);
  };

  return (
    <form 
      onInvalid={(e) => {
        e.preventDefault();
        const t = typeof toast !== 'undefined' ? toast : (window as any).toast;
        if(t) t.error('Por favor, completa todos los campos requeridos.');
      }}
      onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="col-span-1 md:col-span-2">
        <label className="block text-sm font-semibold mb-1 text-foreground">Nombre</label>
        <input type="text" name="nombre" required value={formData.nombre} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" />
      </div>
      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Clases al Mes</label>
        <input type="number" name="clases_por_mes" required min="1" value={formData.clases_por_mes} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" />
      </div>
      <div>
        <label className="block text-sm font-semibold mb-1 text-foreground">Precio ($)</label>
        <input type="text" name="precio" required value={formData.precio} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main" />
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
