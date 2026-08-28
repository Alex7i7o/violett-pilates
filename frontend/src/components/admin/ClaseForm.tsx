import React, { useState, useEffect } from 'react';
import { Button } from '../ui/Button';

export interface ClaseFormData {
  nombre: string;
  descripcion: string;
  duracion_minutos: number;
  cupo_maximo: number;
  cupo_minimo: number;
}

interface ClaseFormProps {
  initialData?: ClaseFormData | null;
  onSubmit: (data: ClaseFormData) => Promise<void>;
  onCancel: () => void;
  isEditing: boolean;
}

export function ClaseForm({ initialData, onSubmit, onCancel, isEditing }: ClaseFormProps) {
  const [formData, setFormData] = useState<ClaseFormData>({
    nombre: '',
    descripcion: '',
    duracion_minutos: 60,
    cupo_maximo: 10,
    cupo_minimo: 1
  });

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      setFormData({ nombre: '', descripcion: '', duracion_minutos: 60, cupo_maximo: 10, cupo_minimo: 1 });
    }
  }, [initialData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ 
        ...prev, 
        [name]: name === 'nombre' || name === 'descripcion' ? value : Number(value) 
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="col-span-1 md:col-span-4">
        <label className="block text-sm font-semibold mb-1 text-foreground">Nombre de la Disciplina</label>
        <input type="text" name="nombre" required value={formData.nombre} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" placeholder="Ej. Pilates Reformer" />
      </div>
      <div className="col-span-1 md:col-span-4">
        <label className="block text-sm font-semibold mb-1 text-foreground">Descripci&oacute;n</label>
        <textarea name="descripcion" value={formData.descripcion} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500 resize-none h-20" placeholder="Opcional..." />
      </div>
      <div className="col-span-1 md:col-span-1">
        <label className="block text-sm font-semibold mb-1 text-foreground">Duraci&oacute;n (min)</label>
        <input type="number" name="duracion_minutos" required min="1" value={formData.duracion_minutos} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
      </div>
      <div className="col-span-1 md:col-span-1">
        <label className="block text-sm font-semibold mb-1 text-foreground">Cupo M&aacute;ximo</label>
        <input type="number" name="cupo_maximo" required min="1" value={formData.cupo_maximo} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
      </div>
      <div className="col-span-1 md:col-span-1">
        <label className="block text-sm font-semibold mb-1 text-foreground">Cupo M&iacute;nimo</label>
        <input type="number" name="cupo_minimo" required min="1" value={formData.cupo_minimo} onChange={handleChange} className="w-full p-2.5 rounded-xl border border-violett-200 focus:outline-none focus:ring-2 focus:ring-violett-500" />
      </div>
      <div className="col-span-1 md:col-span-4 flex justify-end gap-3 mt-2">
        {isEditing && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
        )}
        <Button type="submit">
          {isEditing ? 'Guardar Cambios' : 'Crear Disciplina'}
        </Button>
      </div>
    </form>
  );
}
