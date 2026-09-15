import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { Edit2, Trash2 } from 'lucide-react';

export const ServiciosAdmin = () => {
  const [servicios, setServicios] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<any>(null);
  
  const [nombre, setNombre] = useState('');
  const [precio, setPrecio] = useState('');
  const [duracion, setDuracion] = useState('');
  const [imagen, setImagen] = useState<File | null>(null);

  const fetchServicios = () => {
    api.get('/servicios/')
      .then(res => setServicios(res.data))
      .catch(() => toast.error('Error al cargar servicios'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchServicios();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const data = { nombre, precio_base: parseFloat(precio), duracion_minutos: parseInt(duracion) };
    
    try {
      if (editing) {
        await api.patch(`/servicios/${editing.id}/`, data);
        toast.success('Servicio actualizado');
      } else {
        await api.post('/servicios/', data);
        toast.success('Servicio creado');
      }
      setNombre(''); setPrecio(''); setDuracion(''); setImagen(null); setEditing(null);
      fetchServicios();
    } catch (error) {
      toast.error('Error al guardar servicio');
    }
  };

  const handleEdit = (s: any) => {
    setEditing(s);
    setNombre(s.nombre);
    setPrecio(s.precio_base);
    setDuracion(s.duracion_minutos);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('¿Seguro que deseas eliminar este servicio?')) return;
    try {
      await api.delete(`/servicios/${id}/`);
      toast.success('Servicio eliminado');
      fetchServicios();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  return (
    <div className="w-full">
      <h1 className="text-3xl font-bold text-primary-main mb-8">Gestión de Servicios</h1>
      
      {/* Listado */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-neutral-100 mb-8">
        {loading ? <p className="text-neutral-500">Cargando...</p> : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-neutral-100 text-neutral-500 text-sm">
                  <th className="pb-3 font-medium">Título</th>
                  <th className="pb-3 font-medium">Precio</th>
                  <th className="pb-3 font-medium">Duración</th>
                  <th className="pb-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-50">
                {servicios.map(s => (
                  <tr key={s.id}>
                    <td className="py-4 font-bold text-neutral-800">{s.nombre}</td>
                    <td className="py-4">${s.precio_base}</td>
                    <td className="py-4">{s.duracion_minutos} min</td>
                    <td className="py-4 flex gap-2">
                      <button onClick={() => handleEdit(s)} className="p-2 bg-neutral-800 text-white rounded-lg hover:bg-neutral-900"><Edit2 size={16}/></button>
                      <button onClick={() => handleDelete(s.id)} className="p-2 bg-rose-500 text-white rounded-lg hover:bg-rose-600"><Trash2 size={16}/></button>
                    </td>
                  </tr>
                ))}
                {servicios.length === 0 && (
                  <tr><td colSpan={4} className="py-4 text-neutral-500">No hay servicios configurados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Formulario */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-neutral-100">
        <h2 className="text-xl font-bold text-neutral-800 mb-4">{editing ? 'Editar Servicio' : 'Crear Nuevo Servicio'}</h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm text-neutral-600 mb-1">Nombre</label>
            <input required type="text" value={nombre} onChange={e=>setNombre(e.target.value)} className="w-full p-3 rounded-xl border border-neutral-200 outline-none focus:border-primary-main" />
          </div>
          <div>
            <label className="block text-sm text-neutral-600 mb-1">Precio ($)</label>
            <input required type="number" step="0.01" value={precio} onChange={e=>setPrecio(e.target.value)} className="w-full p-3 rounded-xl border border-neutral-200 outline-none focus:border-primary-main" />
          </div>
          <div>
            <label className="block text-sm text-neutral-600 mb-1">Duración (min)</label>
            <input required type="number" value={duracion} onChange={e=>setDuracion(e.target.value)} className="w-full p-3 rounded-xl border border-neutral-200 outline-none focus:border-primary-main" />
          </div>
          <div className="sm:col-span-3 flex justify-end gap-2 mt-4">
            {editing && <button type="button" onClick={() => {setEditing(null); setNombre(''); setPrecio(''); setDuracion('');}} className="px-6 py-3 bg-neutral-100 text-neutral-600 font-bold rounded-xl hover:bg-neutral-200">Cancelar</button>}
            <button type="submit" className="px-6 py-3 bg-primary-main text-white font-bold rounded-xl hover:bg-primary-hover transition-colors">
              {editing ? 'Guardar Cambios' : 'Crear Servicio'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
