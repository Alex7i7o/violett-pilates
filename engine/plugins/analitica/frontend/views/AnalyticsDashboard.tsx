import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Calendar, DollarSign, TrendingUp, Users, Clock, Mail, MessageCircle, AlertCircle } from 'lucide-react';

const COLORS = ['#34236F', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function AnalyticsDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/analitica/dashboard/?month=${month}&year=${year}`);
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [month, year]);

  if (loading || !data) return <div className="p-8 text-center text-neutral-500">Cargando métricas...</div>;

  const { valor, comunidad, facturacion, operatividad } = data;

  // Format data for charts
  const ageData = Object.entries(comunidad.distribucion_edad).map(([name, value]) => ({ name, value }));
  const genderData = Object.entries(comunidad.distribucion_genero).map(([name, value]) => ({ name, value }));
  const planData = facturacion.desglose_planes.map((p: any) => ({ name: p.plan_nombre, total: parseFloat(p.total) }));

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold font-laluxes text-primary-main">Inteligencia de Negocio</h1>
          <p className="text-neutral-500 font-marcellus">Visualiza el impacto y rendimiento de tu estudio</p>
        </div>
        <div className="flex gap-4">
          <select value={month} onChange={e => setMonth(parseInt(e.target.value))} className="p-2 border rounded-xl bg-white shadow-sm">
            {Array.from({ length: 12 }).map((_, i) => (
              <option key={i} value={i + 1}>{new Date(2000, i).toLocaleString('es', { month: 'long' })}</option>
            ))}
          </select>
          <select value={year} onChange={e => setYear(parseInt(e.target.value))} className="p-2 border rounded-xl bg-white shadow-sm">
            {[2024, 2025, 2026, 2027].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      {/* MOTOR DE VALOR */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-primary-main to-primary-hover p-6 rounded-3xl text-white shadow-lg col-span-1 md:col-span-2">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="w-6 h-6 opacity-80" />
            <h3 className="text-lg font-marcellus">Tiempo Administrativo Ahorrado</h3>
          </div>
          <div className="text-5xl font-bold font-laluxes mb-2">{valor.horas_ahorradas} hs</div>
          <p className="text-primary-light text-sm opacity-90">Este mes el sistema trabajó por vos gestionando turnos y mensajes automáticamente.</p>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-sm flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-2 text-neutral-500"><TrendingUp size={20} /> Tasa de Auto-gestión</div>
          <div className="text-4xl font-bold text-emerald-500">{valor.tasa_autogestion}%</div>
          <p className="text-xs text-neutral-400 mt-1">Alumnos gestionaron sus reservas sin intervención humana</p>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-sm">
          <h3 className="text-sm text-neutral-500 mb-4">Automatizaciones</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="flex items-center gap-2 text-sm font-medium"><Mail size={16} className="text-primary-main"/> Emails</span>
              <span className="font-bold">{valor.emails_enviados}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="flex items-center gap-2 text-sm font-medium"><MessageCircle size={16} className="text-emerald-500"/> WhatsApps</span>
              <span className="font-bold">{valor.wpps_enviados}</span>
            </div>
          </div>
        </div>
      </div>

      {/* FACTURACIÓN Y FINANZAS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-sm">
          <div className="flex items-center gap-2 mb-2 text-neutral-500"><DollarSign size={20} /> Ingresos del Mes</div>
          <div className="text-4xl font-bold text-neutral-800">${facturacion.total.toLocaleString('es-AR')}</div>
          <p className="text-xs text-neutral-400 mt-1">Total recaudado por venta de planes</p>
        </div>
        
        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-sm col-span-1 lg:col-span-2 h-64">
          <h3 className="font-semibold text-neutral-700 mb-4">Desglose de Ingresos por Plan</h3>
          <ResponsiveContainer width="100%" height="80%">
            <BarChart data={planData}>
              <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip cursor={{fill: '#f5f5f5'}} formatter={(val: number) => `$${val.toLocaleString('es-AR')}`} />
              <Bar dataKey="total" fill="#34236F" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* COMUNIDAD */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-sm flex flex-col justify-center items-center text-center">
          <Users className="w-8 h-8 text-primary-main mb-2" />
          <div className="text-4xl font-bold text-neutral-800">{comunidad.total_alumnos}</div>
          <div className="text-sm text-neutral-500">Alumnos Activos</div>
          <div className="mt-2 text-xs font-semibold text-emerald-500 bg-emerald-50 px-2 py-1 rounded-full">+{comunidad.nuevos_alumnos} nuevos este mes</div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-sm h-64">
          <h3 className="font-semibold text-neutral-700 mb-2">Edades (Promedio: {comunidad.promedio_edad})</h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={ageData}>
              <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip cursor={{fill: '#f5f5f5'}} />
              <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-sm h-64">
          <h3 className="font-semibold text-neutral-700 text-center mb-2">Género</h3>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={genderData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                {genderData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* OPERATIVIDAD */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-neutral-900 text-white p-6 rounded-3xl shadow-lg flex flex-col justify-center items-center">
          <div className="text-5xl font-bold mb-2">{operatividad.promedio_ocupacion}%</div>
          <div className="text-sm text-neutral-400">Ocupación Promedio de Clases</div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-sm col-span-1 md:col-span-2">
          <h3 className="font-semibold text-neutral-700 mb-4 flex items-center gap-2"><AlertCircle size={18}/> Dinámica de Clases</h3>
          <div className="flex gap-8">
            <div>
              <div className="text-3xl font-bold text-neutral-800">{operatividad.clases_dictadas}</div>
              <div className="text-sm text-neutral-500">Clases dictadas</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-red-500">{operatividad.clases_canceladas}</div>
              <div className="text-sm text-neutral-500">Clases canceladas</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
