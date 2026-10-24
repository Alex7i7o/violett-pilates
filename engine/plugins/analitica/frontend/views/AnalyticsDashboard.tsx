import React, { useEffect, useState, useMemo } from 'react';
import { api } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { 
  Calendar, DollarSign, TrendingUp, Users, Clock, Mail, MessageCircle, AlertCircle, 
  Send, CheckCircle2, XCircle, Search, ChevronRight, Phone, CreditCard, Sparkles, User, 
  Filter, X, ArrowUpRight, Check
} from 'lucide-react';
import { Modal } from '@/components/ui/Modal';

const COLORS = ['#34236F', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

interface FacturacionDetalle {
  id: string;
  fecha: string;
  fecha_corta: string;
  alumno_id: string | null;
  alumno_nombre: string;
  alumno_email: string;
  alumno_telefono: string;
  plan_nombre: string;
  monto: number;
  suscripcion_id: string | null;
  suscripcion_estado: string | null;
  clases_restantes: number | null;
  clases_totales: number | null;
  fecha_vencimiento: string | null;
}

export default function AnalyticsDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [testingEmail, setTestingEmail] = useState(false);
  const [emailStatus, setEmailStatus] = useState<{ success: boolean; detail: string } | null>(null);

  // Modal de desglose de facturación
  const [showBillingModal, setShowBillingModal] = useState(false);
  const [billingSearch, setBillingSearch] = useState('');
  const [selectedPlanFilter, setSelectedPlanFilter] = useState('ALL');
  const [billingSort, setBillingSort] = useState<'fecha_desc' | 'fecha_asc' | 'monto_desc' | 'monto_asc' | 'nombre'>('fecha_desc');

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

  const handleTestEmail = async () => {
    setTestingEmail(true);
    setEmailStatus(null);
    try {
      const res = await api.post('/analitica/test-email/');
      setEmailStatus({ success: true, detail: res.data.detail });
      fetchData();
    } catch (e: any) {
      const detail = e.response?.data?.detail || e.message || 'Error al enviar correo de prueba.';
      setEmailStatus({ success: false, detail });
    } finally {
      setTestingEmail(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [month, year]);

  const monthName = useMemo(() => {
    const raw = new Date(year, month - 1, 1).toLocaleString('es', { month: 'long' });
    return raw.charAt(0).toUpperCase() + raw.slice(1);
  }, [month, year]);

  const billingRecords: FacturacionDetalle[] = useMemo(() => {
    return data?.facturacion?.detalles || [];
  }, [data]);

  // Registros filtrados y ordenados para el modal
  const filteredBillingRecords = useMemo(() => {
    return billingRecords
      .filter((item) => {
        const matchesPlan = selectedPlanFilter === 'ALL' || item.plan_nombre === selectedPlanFilter;
        if (!matchesPlan) return false;
        if (!billingSearch.trim()) return true;
        const q = billingSearch.toLowerCase().trim();
        return (
          item.alumno_nombre.toLowerCase().includes(q) ||
          item.alumno_email.toLowerCase().includes(q) ||
          item.alumno_telefono.toLowerCase().includes(q) ||
          item.plan_nombre.toLowerCase().includes(q)
        );
      })
      .sort((a, b) => {
        if (billingSort === 'fecha_asc') return a.fecha.localeCompare(b.fecha);
        if (billingSort === 'fecha_desc') return b.fecha.localeCompare(a.fecha);
        if (billingSort === 'monto_desc') return b.monto - a.monto;
        if (billingSort === 'monto_asc') return a.monto - b.monto;
        if (billingSort === 'nombre') return a.alumno_nombre.localeCompare(b.alumno_nombre);
        return 0;
      });
  }, [billingRecords, billingSearch, selectedPlanFilter, billingSort]);

  const filteredTotal = useMemo(() => {
    return filteredBillingRecords.reduce((acc, curr) => acc + (curr.monto || 0), 0);
  }, [filteredBillingRecords]);

  if (loading || !data) return <div className="p-8 text-center text-neutral-500 font-marcellus">Cargando métricas...</div>;

  const { valor, comunidad, facturacion, operatividad } = data;

  // Format data for charts
  const ageData = Object.entries(comunidad.distribucion_edad).map(([name, value]) => ({ name, value }));
  const genderData = Object.entries(comunidad.distribucion_genero).map(([name, value]) => ({ name, value }));
  const planData = facturacion.desglose_planes.map((p: any) => ({ name: p.plan_nombre, total: parseFloat(p.total) }));

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto space-y-6">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold font-laluxes text-primary-main">Inteligencia de Negocio</h1>
          <p className="text-neutral-500 font-marcellus text-sm sm:text-base">Visualiza el impacto y rendimiento de tu estudio</p>
        </div>
        <div className="flex gap-2 sm:gap-4 w-full sm:w-auto">
          <select 
            value={month} 
            onChange={e => setMonth(parseInt(e.target.value))} 
            className="flex-1 sm:flex-none p-2 sm:px-3 sm:py-2 border border-neutral-200 rounded-xl bg-white shadow-xs text-sm font-medium text-neutral-700 focus:outline-none focus:ring-2 focus:ring-primary-main/20"
          >
            {Array.from({ length: 12 }).map((_, i) => (
              <option key={i} value={i + 1}>{new Date(2000, i).toLocaleString('es', { month: 'long' })}</option>
            ))}
          </select>
          <select 
            value={year} 
            onChange={e => setYear(parseInt(e.target.value))} 
            className="p-2 sm:px-3 sm:py-2 border border-neutral-200 rounded-xl bg-white shadow-xs text-sm font-medium text-neutral-700 focus:outline-none focus:ring-2 focus:ring-primary-main/20"
          >
            {[2024, 2025, 2026, 2027].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
      </div>

      {emailStatus && (
        <div className={`p-4 rounded-2xl flex items-start gap-3 text-sm animate-fade-in ${emailStatus.success ? 'bg-emerald-50 text-emerald-900 border border-emerald-200' : 'bg-red-50 text-red-900 border border-red-200'}`}>
          {emailStatus.success ? <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" /> : <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />}
          <div className="flex-1">
            <div className="font-semibold">{emailStatus.success ? 'Diagnóstico de Correo Exitoso' : 'Fallo en la Configuración de Correo'}</div>
            <div className="text-xs mt-1 leading-relaxed">{emailStatus.detail}</div>
          </div>
          <button onClick={() => setEmailStatus(null)} className="text-xs font-semibold px-2 py-1 rounded hover:bg-black/5">Cerrar</button>
        </div>
      )}

      {/* MOTOR DE VALOR */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 sm:gap-6">
        <div className="bg-gradient-to-br from-primary-main to-primary-hover p-6 rounded-3xl text-white shadow-lg col-span-1 md:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Clock className="w-6 h-6 opacity-80" />
              <h3 className="text-lg font-marcellus">Tiempo Administrativo Ahorrado</h3>
            </div>
            <div className="text-4xl sm:text-5xl font-bold font-laluxes mb-2">{valor.horas_ahorradas} hs</div>
          </div>
          <p className="text-primary-light text-xs sm:text-sm opacity-90">Este mes el sistema trabajó por vos gestionando turnos y mensajes automáticamente.</p>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-xs flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-2 text-neutral-500 text-sm"><TrendingUp size={20} /> Tasa de Auto-gestión</div>
          <div className="text-4xl font-bold text-emerald-500">{valor.tasa_autogestion}%</div>
          <p className="text-xs text-neutral-400 mt-1">Alumnos gestionaron sus reservas sin intervención humana</p>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="text-sm text-neutral-500 mb-4">Automatizaciones</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="flex items-center gap-2 text-sm font-medium"><Mail size={16} className="text-primary-main"/> Emails</span>
                <span className="font-bold text-neutral-800">{valor.emails_enviados}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="flex items-center gap-2 text-sm font-medium"><MessageCircle size={16} className="text-emerald-500"/> WhatsApps</span>
                <span className="font-bold text-neutral-800">{valor.wpps_enviados}</span>
              </div>
            </div>
          </div>
          <button
            onClick={handleTestEmail}
            disabled={testingEmail}
            className="mt-4 w-full text-xs font-semibold py-2 px-3 rounded-xl border border-primary-main/20 text-primary-main hover:bg-primary-light/50 transition flex items-center justify-center gap-1.5 disabled:opacity-50"
            title="Envía un correo de prueba a tu email para diagnosticar la conexión con Resend"
          >
            <Send size={13} />
            {testingEmail ? 'Comprobando...' : 'Probar Envío de Correo'}
          </button>
        </div>
      </div>

      {/* FACTURACIÓN Y FINANZAS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* CARD INTERACTIVA DE FACTURACIÓN */}
        <div 
          onClick={() => setShowBillingModal(true)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setShowBillingModal(true); } }}
          className="bg-white p-6 rounded-3xl border border-neutral-200/80 shadow-xs hover:border-primary-main/50 hover:shadow-md transition-all duration-200 cursor-pointer group active:scale-[0.99] relative overflow-hidden flex flex-col justify-between"
          title="Toca para ver la lista de alumnos que pagaron y desglosar la facturación"
        >
          {/* Subtle decorative glow */}
          <div className="absolute -top-12 -right-12 w-32 h-32 bg-primary-light/40 rounded-full blur-2xl pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-neutral-500 font-medium text-sm">
                <DollarSign size={20} className="text-primary-main" /> Ingresos del Mes
              </div>
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-primary-main bg-primary-light/60 px-2.5 py-1 rounded-full group-hover:bg-primary-main group-hover:text-white transition-all shadow-xs">
                Ver detalle <ChevronRight size={13} className="transition-transform group-hover:translate-x-0.5" />
              </span>
            </div>
            <div className="text-3xl sm:text-4xl font-bold text-neutral-800 tracking-tight">
              ${facturacion.total.toLocaleString('es-AR')}
            </div>
            <p className="text-xs text-neutral-400 mt-1">Total recaudado por venta de planes</p>
          </div>

          <div className="mt-4 pt-3 border-t border-neutral-100 flex items-center justify-between text-xs">
            <span className="text-neutral-500 font-medium">
              {billingRecords.length} {billingRecords.length === 1 ? 'plan registrado' : 'planes registrados'}
            </span>
            <span className="font-semibold text-primary-main flex items-center gap-1 group-hover:underline">
              Desglosar facturación ↗
            </span>
          </div>
        </div>
        
        {/* GRÁFICO DESGLOSE POR PLAN */}
        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-xs col-span-1 lg:col-span-2 h-64">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-neutral-700 text-sm sm:text-base">Desglose de Ingresos por Plan</h3>
            <span className="text-xs text-neutral-400 font-marcellus">{monthName} {year}</span>
          </div>
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-xs flex flex-col justify-center items-center text-center">
          <Users className="w-8 h-8 text-primary-main mb-2" />
          <div className="text-4xl font-bold text-neutral-800">{comunidad.total_alumnos}</div>
          <div className="text-sm text-neutral-500">Alumnos Activos</div>
          <div className="mt-2 text-xs font-semibold text-emerald-500 bg-emerald-50 px-2 py-1 rounded-full">+{comunidad.nuevos_alumnos} nuevos este mes</div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-xs h-64">
          <h3 className="font-semibold text-neutral-700 mb-2 text-sm sm:text-base">Edades (Promedio: {comunidad.promedio_edad})</h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={ageData}>
              <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip cursor={{fill: '#f5f5f5'}} />
              <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-xs h-64">
          <h3 className="font-semibold text-neutral-700 text-center mb-2 text-sm sm:text-base">Género</h3>
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
        <div className="bg-neutral-900 text-white p-6 rounded-3xl shadow-lg flex flex-col justify-center items-center">
          <div className="text-4xl sm:text-5xl font-bold mb-2">{operatividad.promedio_ocupacion}%</div>
          <div className="text-sm text-neutral-400">Ocupación Promedio de Clases</div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-neutral-100 shadow-xs col-span-1 md:col-span-2">
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

      {/* MODAL DESGLOSE DE FACTURACIÓN */}
      <Modal 
        isOpen={showBillingModal} 
        onClose={() => setShowBillingModal(false)}
        title={`Desglose de Facturación - ${monthName} ${year}`}
        className="sm:max-w-4xl"
      >
        <div className="space-y-5">
          {/* MINI RESUMEN */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-primary-light/40 border border-primary-main/15 rounded-2xl p-3.5">
              <span className="text-xs font-medium text-primary-main block">Total Recaudado</span>
              <span className="text-2xl font-bold font-laluxes text-primary-main">
                ${facturacion.total.toLocaleString('es-AR')}
              </span>
              <span className="text-[11px] text-neutral-500 block mt-0.5">
                {billingRecords.length} {billingRecords.length === 1 ? 'plan registrado' : 'planes registrados'}
              </span>
            </div>

            <div className="bg-neutral-50 border border-neutral-200/80 rounded-2xl p-3.5">
              <span className="text-xs font-medium text-neutral-500 block">Total Filtrado</span>
              <span className="text-2xl font-bold font-laluxes text-neutral-800">
                ${filteredTotal.toLocaleString('es-AR')}
              </span>
              <span className="text-[11px] text-neutral-400 block mt-0.5">
                {filteredBillingRecords.length} de {billingRecords.length} en pantalla
              </span>
            </div>

            <div className="bg-emerald-50/60 border border-emerald-200/60 rounded-2xl p-3.5">
              <span className="text-xs font-medium text-emerald-700 block">Ticket Promedio</span>
              <span className="text-2xl font-bold font-laluxes text-emerald-800">
                ${billingRecords.length > 0 ? Math.round(facturacion.total / billingRecords.length).toLocaleString('es-AR') : '0'}
              </span>
              <span className="text-[11px] text-emerald-600/80 block mt-0.5">por alumno / plan</span>
            </div>
          </div>

          {/* BUSCADOR Y FILTROS */}
          <div className="flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400 pointer-events-none" />
              <input
                type="text"
                placeholder="Buscar por alumno, email, teléfono o plan..."
                value={billingSearch}
                onChange={e => setBillingSearch(e.target.value)}
                className="w-full pl-9 pr-8 py-2 text-sm bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-main/20 focus:border-primary-main transition-colors"
              />
              {billingSearch && (
                <button
                  type="button"
                  onClick={() => setBillingSearch('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600 p-0.5"
                >
                  <X size={14} />
                </button>
              )}
            </div>

            {/* ORDENAMIENTO */}
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-xs text-neutral-400 hidden sm:inline">Ordenar:</span>
              <select
                value={billingSort}
                onChange={e => setBillingSort(e.target.value as any)}
                className="text-xs font-medium bg-neutral-50 border border-neutral-200 rounded-xl px-2.5 py-2 text-neutral-700 focus:outline-none focus:ring-2 focus:ring-primary-main/20"
              >
                <option value="fecha_desc">Fecha (más reciente)</option>
                <option value="fecha_asc">Fecha (más antigua)</option>
                <option value="monto_desc">Monto (mayor a menor)</option>
                <option value="monto_asc">Monto (menor a mayor)</option>
                <option value="nombre">Alumno (A-Z)</option>
              </select>
            </div>
          </div>

          {/* CHIPS DE FILTRO POR PLAN */}
          {facturacion.desglose_planes && facturacion.desglose_planes.length > 0 && (
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar text-xs">
              <span className="text-neutral-400 shrink-0 flex items-center gap-1 mr-1">
                <Filter size={12} /> Planes:
              </span>
              <button
                type="button"
                onClick={() => setSelectedPlanFilter('ALL')}
                className={`px-3 py-1 rounded-full font-medium transition-all shrink-0 ${
                  selectedPlanFilter === 'ALL'
                    ? 'bg-primary-main text-white shadow-xs'
                    : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
                }`}
              >
                Todos ({billingRecords.length})
              </button>
              {facturacion.desglose_planes.map((p: any) => (
                <button
                  key={p.plan_nombre}
                  type="button"
                  onClick={() => setSelectedPlanFilter(p.plan_nombre)}
                  className={`px-3 py-1 rounded-full font-medium transition-all shrink-0 ${
                    selectedPlanFilter === p.plan_nombre
                      ? 'bg-primary-main text-white shadow-xs'
                      : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
                  }`}
                >
                  {p.plan_nombre} ({p.cantidad})
                </button>
              ))}
            </div>
          )}

          {/* LISTA / TABLA DE REGISTROS */}
          {filteredBillingRecords.length === 0 ? (
            <div className="py-12 text-center text-neutral-400 bg-neutral-50/60 rounded-2xl border border-dashed border-neutral-200">
              <DollarSign className="w-10 h-10 mx-auto text-neutral-300 mb-2 stroke-[1.5]" />
              <p className="text-sm font-semibold text-neutral-600">
                {billingRecords.length === 0 
                  ? `No se registraron ventas ni planes asignados en ${monthName} ${year}.`
                  : 'No se encontraron cobros que coincidan con la búsqueda.'}
              </p>
              {billingSearch && (
                <button
                  type="button"
                  onClick={() => { setBillingSearch(''); setSelectedPlanFilter('ALL'); }}
                  className="mt-2 text-xs text-primary-main font-semibold hover:underline"
                >
                  Limpiar filtros
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {/* VISTA MOBILE: TARJETAS */}
              <div className="block sm:hidden space-y-2.5">
                {filteredBillingRecords.map((item) => {
                  const initials = item.alumno_nombre
                    ? item.alumno_nombre.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase()
                    : 'AL';

                  return (
                    <div 
                      key={item.id} 
                      className="bg-white border border-neutral-200/80 rounded-2xl p-3.5 shadow-2xs space-y-2"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="w-9 h-9 rounded-full bg-primary-light/60 text-primary-main font-bold text-xs flex items-center justify-center shrink-0">
                            {initials}
                          </div>
                          <div className="min-w-0">
                            <h4 className="font-semibold text-sm text-neutral-800 truncate">
                              {item.alumno_nombre}
                            </h4>
                            <p className="text-[11px] text-neutral-400 truncate">{item.alumno_email || 'Sin email registrado'}</p>
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="text-base font-bold text-neutral-900 block font-laluxes">
                            ${item.monto.toLocaleString('es-AR')}
                          </span>
                          <span className="text-[10px] text-neutral-400 block">{item.fecha_corta}</span>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center justify-between gap-1.5 pt-2 border-t border-neutral-100 text-xs">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-primary-light/50 text-primary-main border border-primary-main/15">
                          {item.plan_nombre}
                        </span>

                        {item.suscripcion_estado ? (
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium border ${
                            item.suscripcion_estado === 'ACTIVO'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : item.suscripcion_estado === 'AGOTADO'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : item.suscripcion_estado === 'CANCELADO'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-neutral-100 text-neutral-600 border-neutral-200'
                          }`}>
                            {item.suscripcion_estado === 'ACTIVO' && (
                              <>Activo • {item.clases_restantes ?? 0}/{item.clases_totales ?? '—'} clases</>
                            )}
                            {item.suscripcion_estado === 'AGOTADO' && 'Agotado'}
                            {item.suscripcion_estado === 'VENCIDO' && 'Vencido'}
                            {item.suscripcion_estado === 'CANCELADO' && 'Cancelado'}
                          </span>
                        ) : (
                          <span className="text-[11px] text-neutral-400">Plan asignado</span>
                        )}

                        {item.alumno_telefono && (
                          <a
                            href={`https://wa.me/${item.alumno_telefono.replace(/[^0-9]/g, '')}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] text-emerald-600 font-medium hover:underline ml-auto"
                            title="Contactar por WhatsApp"
                          >
                            <Phone size={11} /> {item.alumno_telefono}
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* VISTA DESKTOP / TABLET: TABLA */}
              <div className="hidden sm:block overflow-x-auto rounded-2xl border border-neutral-200/80">
                <table className="w-full text-left text-xs">
                  <thead className="bg-neutral-50/80 text-neutral-500 font-medium border-b border-neutral-200/80">
                    <tr>
                      <th className="py-3 px-4">Fecha</th>
                      <th className="py-3 px-4">Alumno</th>
                      <th className="py-3 px-4">Plan Adquirido</th>
                      <th className="py-3 px-4">Estado Membresía</th>
                      <th className="py-3 px-4 text-right">Monto</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100">
                    {filteredBillingRecords.map((item) => {
                      const initials = item.alumno_nombre
                        ? item.alumno_nombre.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase()
                        : 'AL';

                      return (
                        <tr key={item.id} className="hover:bg-primary-light/10 transition-colors">
                          <td className="py-3 px-4 whitespace-nowrap text-neutral-500 font-mono text-[11px]">
                            {item.fecha || item.fecha_corta}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2.5">
                              <div className="w-8 h-8 rounded-full bg-primary-light/60 text-primary-main font-bold text-xs flex items-center justify-center shrink-0">
                                {initials}
                              </div>
                              <div className="min-w-0">
                                <span className="font-semibold text-neutral-800 text-sm block truncate">
                                  {item.alumno_nombre}
                                </span>
                                <div className="flex items-center gap-2 text-[11px] text-neutral-400">
                                  {item.alumno_email && <span className="truncate">{item.alumno_email}</span>}
                                  {item.alumno_telefono && (
                                    <a
                                      href={`https://wa.me/${item.alumno_telefono.replace(/[^0-9]/g, '')}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-0.5 text-emerald-600 hover:underline shrink-0"
                                      title="Enviar WhatsApp"
                                    >
                                      <Phone size={10} /> {item.alumno_telefono}
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-1 rounded-full font-semibold text-xs bg-primary-light/50 text-primary-main border border-primary-main/15">
                              {item.plan_nombre}
                            </span>
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            {item.suscripcion_estado ? (
                              <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                                item.suscripcion_estado === 'ACTIVO'
                                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                  : item.suscripcion_estado === 'AGOTADO'
                                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                                  : item.suscripcion_estado === 'CANCELADO'
                                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                                  : 'bg-neutral-100 text-neutral-600 border-neutral-200'
                              }`}>
                                {item.suscripcion_estado === 'ACTIVO' && (
                                  <>Activo ({item.clases_restantes ?? 0}/{item.clases_totales ?? '—'} clases)</>
                                )}
                                {item.suscripcion_estado === 'AGOTADO' && 'Agotado'}
                                {item.suscripcion_estado === 'VENCIDO' && 'Vencido'}
                                {item.suscripcion_estado === 'CANCELADO' && 'Cancelado'}
                              </span>
                            ) : (
                              <span className="text-neutral-400 text-xs italic">Cobro registrado</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right whitespace-nowrap">
                            <span className="text-sm font-bold text-neutral-900 font-laluxes">
                              ${item.monto.toLocaleString('es-AR')}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* FOOTER DEL MODAL */}
          <div className="pt-3 border-t border-neutral-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-neutral-500">
            <div>
              Mostrando <strong className="text-neutral-800">{filteredBillingRecords.length}</strong> de <strong className="text-neutral-800">{billingRecords.length}</strong> registros
              {billingSearch && <span> (filtrado por "{billingSearch}")</span>}
            </div>
            <button
              type="button"
              onClick={() => setShowBillingModal(false)}
              className="w-full sm:w-auto px-4 py-2 bg-neutral-100 hover:bg-neutral-200 text-neutral-700 font-semibold rounded-xl transition"
            >
              Cerrar
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
