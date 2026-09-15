import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { Edit2, Trash2 } from 'lucide-react';

export const ReglasAdmin = () => {
  const [reglas, setReglas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<any>(null);
  
  const [sesiones, setSesiones] = useState('');
  const [descuento, setDescuento] = useState('');

  const fetchReglas = () => {
    api.get('/reglas-paquetes/')
      .then(res => setReglas(res.data))
      .catch(() => toast.error('Error al cargar reglas'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchReglas();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const data = { cantidad_sesiones: parseInt(sesiones), descuento_porcentaje: parseFloat(descuento) };
    
    try {
      if (editing) {
        await api.patch(`/reglas-paquetes/${editing.id}/`, data);
        toast.success('Regla actualizada');
      } else {
        await api.post('/reglas-paquetes/', data);
        toast.success('Regla creada');
      }
      setSesiones(''); setDescuento(''); setEditing(null);
      fetchReglas();
    } catch (error) {
      toast.error('Error al guardar regla');
    }
  };

  const handleEdit = (r: any) => {
    setEditing(r);
    setSesiones(r.cantidad_sesiones);
    setDescuento(r.descuento_porcentaje);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('¿Seguro que deseas eliminar esta regla?')) return;
    try {
      await api.delete(`/reglas-paquetes/${id}/`);
      toast.success('Regla eliminada');
      fetchReglas();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };

  return (
    <div className="w-full">
      <h1 className="text-3xl font-bold text-primary-main mb-2">Configuración de Paquetes de Venta</h1>
      <p className="text-neutral-600 mb-8">Definí las opciones de cantidad de sesiones y descuentos que verán los clientes.</p>
      
      {/* Listado */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-neutral-100 mb-8">
        {loading ? <p className="text-neutral-500">Cargando...</p> : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-neutral-100 text-neutral-500 text-sm">
                  <th className="pb-3 font-medium">Sesiones</th>
                  <th className="pb-3 font-medium">Descuento (%)</th>
                  <th className="pb-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-50">
                {reglas.map(r => (
                  <tr key={r.id}>
                    <td className="py-4 font-bold text-neutral-800">{r.cantidad_sesiones} {r.cantidad_sesiones === 1 ? 'sesión' : 'sesiones'}</td>
                    <td className="py-4">{parseFloat(r.descuento_porcentaje)}%</td>
                    <td className="py-4 flex gap-2">
                      <button onClick={() => handleEdit(r)} className="px-4 py-2 bg-neutral-800 text-white text-sm rounded hover:bg-neutral-900 transition">Modificar</button>
                      <button onClick={() => handleDelete(r.id)} className="px-4 py-2 bg-rose-500 text-white text-sm rounded hover:bg-rose-600 transition">Eliminar</button>
                    </td>
                  </tr>
                ))}
                {reglas.length === 0 && (
                  <tr><td colSpan={3} className="py-4 text-neutral-500">No hay reglas configuradas.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Formulario */}
      <div className="bg-neutral-50 p-6 rounded-2xl shadow-sm border border-neutral-100">
        <h2 className="text-xl font-bold text-neutral-800 mb-4">{editing ? 'Modificar Opción' : 'Añadir Nueva Opción'}</h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-6 items-end">
          <div>
            <label className="block text-sm text-neutral-600 font-bold mb-2">Cantidad de Sesiones</label>
            <select required value={sesiones} onChange={e=>setSesiones(e.target.value)} className="w-full p-3 rounded-xl border border-neutral-200 outline-none focus:border-primary-main bg-white">
                <option value="">Seleccionar cantidad</option>
                {[...Array(20)].map((_, i) => <option key={i+1} value={i+1}>{i+1}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-neutral-600 font-bold mb-2">Descuento (%)</label>
            <select required value={descuento} onChange={e=>setDescuento(e.target.value)} className="w-full p-3 rounded-xl border border-neutral-200 outline-none focus:border-primary-main bg-white">
                <option value="">Seleccionar descuento</option>
                {[0, 5, 10, 15, 20, 25, 30, 40, 50].map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div className="sm:col-span-2 flex justify-end gap-2 mt-2">
            {editing && <button type="button" onClick={() => {setEditing(null); setSesiones(''); setDescuento('');}} className="px-6 py-3 bg-neutral-200 text-neutral-600 font-bold rounded-xl hover:bg-neutral-300">Cancelar</button>}
            <button type="submit" className="px-6 py-3 bg-indigo-800 text-white font-bold rounded-xl hover:bg-indigo-900 transition-colors">
              {editing ? 'Guardar Cambios' : 'Añadir Opción'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
