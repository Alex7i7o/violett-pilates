import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { ShoppingBag, Tag, ChevronDown } from 'lucide-react';

export const TiendaPaquetes = () => {
  const [servicios, setServicios] = useState<any[]>([]);
  const [reglas, setReglas] = useState<any[]>([]);

  const [selectedServicio, setSelectedServicio] = useState('');
  const [selectedRegla, setSelectedRegla] = useState('');

  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/servicios/'),
      api.get('/reglas-paquetes/')
    ])
    .then(([resServicios, resReglas]) => {
      setServicios(resServicios.data.filter((s:any) => s.is_active));
      setReglas(resReglas.data.filter((r:any) => r.is_active));

      if (resServicios.data.length > 0) setSelectedServicio(resServicios.data[0].id);
      if (resReglas.data.length > 0) setSelectedRegla(resReglas.data[0].id);
    })
    .catch(() => toast.error('Error cargando la tienda'))
    .finally(() => setLoading(false));
  }, []);

  const handleBuy = async () => {
    if (!selectedServicio || !selectedRegla) return;
    setBuying(true);
    try {
      const res = await api.post('/pagos/checkout/', { 
          servicio_id: selectedServicio, 
          regla_id: selectedRegla 
      });
      if (res.data.init_point) {
        window.location.href = res.data.init_point;
      } else {
        toast.error('No se pudo generar el link de pago');
        setBuying(false);
      }
    } catch (error) {
      toast.error('Error al iniciar el pago');
      setBuying(false);
    }
  };

  const currentServicio = servicios.find(s => s.id === selectedServicio);
  const currentRegla = reglas.find(r => r.id === selectedRegla);

  let totalCalculado = 0;
  let porcentajeDescuento = 0;
  if (currentServicio && currentRegla) {
      const precioBase = parseFloat(currentServicio.precio_base);
      const sesiones = parseInt(currentRegla.cantidad_sesiones);
      porcentajeDescuento = parseFloat(currentRegla.descuento_porcentaje);
      totalCalculado = (precioBase * sesiones) * (1 - (porcentajeDescuento / 100));
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', duration: 0.5, bounce: 0.2 } }
  };

  if (loading) {
    return (
      <div className="w-full space-y-6">
        <div className="h-40 bg-neutral-200 rounded-3xl animate-pulse"></div>
        <div className="h-24 bg-neutral-200 rounded-3xl animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="w-full pb-32">
      <motion.div 
        variants={containerVariants} 
        initial="hidden" 
        animate="show"
        className="space-y-6"
      >
        <motion.div variants={itemVariants} className="bg-white rounded-[2rem] p-6 sm:p-8 shadow-sm border border-neutral-100">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-primary-50 text-primary-main rounded-2xl">
              <ShoppingBag size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-neutral-900 tracking-tight">Armá tu paquete</h2>
              <p className="text-sm text-neutral-500">Seleccioná un servicio y sesiones.</p>
            </div>
          </div>

          <div className="space-y-5">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-neutral-700 ml-1">Servicio</label>
              <div className="relative">
                <select 
                  value={selectedServicio} 
                  onChange={e => setSelectedServicio(e.target.value)}
                  className="w-full p-4 pl-5 pr-12 rounded-2xl border-2 border-neutral-100 bg-neutral-50 outline-none focus:border-primary-main focus:bg-white transition-all appearance-none text-neutral-900 font-medium"
                >
                    {servicios.map(s => (
                        <option key={s.id} value={s.id}>{s.nombre} (${parseFloat(s.precio_base)})</option>
                    ))}
                </select>
                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" size={20} />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-neutral-700 ml-1">Cantidad de Sesiones</label>
              <div className="relative">
                <select 
                  value={selectedRegla} 
                  onChange={e => setSelectedRegla(e.target.value)}
                  className="w-full p-4 pl-5 pr-12 rounded-2xl border-2 border-neutral-100 bg-neutral-50 outline-none focus:border-primary-main focus:bg-white transition-all appearance-none text-neutral-900 font-medium"
                >
                    {reglas.map(r => (
                        <option key={r.id} value={r.id}>{r.cantidad_sesiones} Sesión{r.cantidad_sesiones > 1 ? 'es' : ''}</option>
                    ))}
                </select>
                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" size={20} />
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Floating Checkout Bar */}
      <AnimatePresence>
        {currentServicio && currentRegla && (
          <motion.div 
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed bottom-[4.5rem] sm:bottom-8 left-0 right-0 z-40 px-4 sm:px-0 pointer-events-none"
          >
            <div className="max-w-4xl mx-auto flex justify-center">
              <div className="bg-neutral-900 text-white rounded-full shadow-2xl p-2 pl-6 pr-2 flex items-center justify-between w-full max-w-[90%] sm:max-w-md pointer-events-auto">
                <div className="flex flex-col mr-4">
                  <span className="text-xs font-medium text-neutral-400">Total</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xl font-bold">${totalCalculado.toFixed(0)}</span>
                    {porcentajeDescuento > 0 && (
                      <span className="text-[10px] font-bold bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Tag size={10} /> {porcentajeDescuento}% OFF
                      </span>
                    )}
                  </div>
                </div>

                <button 
                  onClick={handleBuy}
                  disabled={buying}
                  className="px-6 py-3.5 bg-primary-main text-primary-contrast font-bold text-sm rounded-full active:scale-95 transition-all disabled:opacity-50 whitespace-nowrap"
                >
                  {buying ? 'PROCESANDO...' : 'PAGAR'}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
