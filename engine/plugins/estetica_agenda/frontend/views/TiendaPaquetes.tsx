import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useClientConfig } from '@/context/ClientConfigContext';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { ShoppingBag, Tag, ChevronDown, Copy, Check, X, MessageCircle } from 'lucide-react';

export const TiendaPaquetes = () => {
  const config = useClientConfig();
  const [servicios, setServicios] = useState<any[]>([]);
  const [reglas, setReglas] = useState<any[]>([]);

  const [selectedServicio, setSelectedServicio] = useState('');
  const [selectedRegla, setSelectedRegla] = useState('');

  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(false);

  // Estado para modal de pago por Alias / Transferencia
  const [aliasModalInfo, setAliasModalInfo] = useState<any | null>(null);
  const [copiedAlias, setCopiedAlias] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get('/servicios/'),
      api.get('/reglas-paquetes/')
    ])
      .then(([resServicios, resReglas]) => {
        const srvActivos = (resServicios.data || []).filter((s: any) => s.is_active);
        const regActivas = (resReglas.data || []).filter((r: any) => r.is_active);
        setServicios(srvActivos);
        setReglas(regActivas);

        if (srvActivos.length > 0) setSelectedServicio(srvActivos[0].id);
        if (regActivas.length > 0) setSelectedRegla(regActivas[0].id);
      })
      .catch(() => toast.error('Error cargando la tienda'))
      .finally(() => setLoading(false));
  }, []);

  const currentServicio = servicios.find(s => s.id === selectedServicio);
  const currentRegla = reglas.find(r => r.id === selectedRegla);

  let totalCalculado = 0;
  let porcentajeDescuento = 0;
  if (currentServicio && currentRegla) {
    const precioBase = parseFloat(currentServicio.precio_base);
    const sesiones = parseInt(currentRegla.cantidad_sesiones);
    porcentajeDescuento = parseFloat(currentRegla.descuento_porcentaje);
    totalCalculado = precioBase * sesiones * (1 - porcentajeDescuento / 100);
  }

  const handleBuy = async () => {
    if (!selectedServicio || !selectedRegla) return;
    setBuying(true);
    try {
      const res = await api.post('/pagos/checkout/', {
        servicio_id: selectedServicio,
        regla_id: selectedRegla
      });
      if (res.data?.init_point) {
        window.location.href = res.data.init_point;
      } else if (res.data?.type === 'alias') {
        setAliasModalInfo(res.data.info || {});
      } else {
        toast.error('No se pudo iniciar el medio de pago.');
      }
    } catch {
      toast.error('Error al iniciar el pago');
    } finally {
      setBuying(false);
    }
  };

  const handleCopyAlias = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedAlias(true);
    toast.success('Alias copiado al portapapeles');
    setTimeout(() => setCopiedAlias(false), 2000);
  };

  const handleWhatsAppComprobante = () => {
    if (!currentServicio || !currentRegla) return;
    const phone = config.contact_phone || '5491164142172';
    const msg = `¡Hola Violett Estética! Realicé la transferencia por el paquete de *${currentRegla.cantidad_sesiones} sesión(es) de ${currentServicio.nombre}* por *$${totalCalculado.toLocaleString('es-AR')}*. Adjunto el comprobante para acreditar en mi billetera:`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(msg)}`, '_blank');
    setAliasModalInfo(null);
  };

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
              <p className="text-sm text-neutral-500">Seleccioná un tratamiento y la cantidad de sesiones.</p>
            </div>
          </div>

          <div className="space-y-5">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-neutral-700 ml-1">Tratamiento</label>
              <div className="relative">
                <select
                  value={selectedServicio}
                  onChange={e => setSelectedServicio(e.target.value)}
                  className="w-full p-4 pl-5 pr-12 rounded-2xl border-2 border-neutral-100 bg-neutral-50 outline-none focus:border-primary-main focus:bg-white transition-all appearance-none text-neutral-900 font-medium"
                >
                  {servicios.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.nombre} (${parseFloat(s.precio_base).toLocaleString('es-AR')} por sesión)
                    </option>
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
                    <option key={r.id} value={r.id}>
                      {r.cantidad_sesiones} Sesión{r.cantidad_sesiones > 1 ? 'es' : ''}
                      {parseFloat(r.descuento_porcentaje) > 0 ? ` (${parseFloat(r.descuento_porcentaje)}% OFF)` : ''}
                    </option>
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
                  <span className="text-xs font-medium text-neutral-400">Total a abonar</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xl font-bold">${totalCalculado.toLocaleString('es-AR')}</span>
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
                  className="px-6 py-3.5 bg-primary-main text-white font-bold text-sm rounded-full active:scale-95 transition-all disabled:opacity-50 whitespace-nowrap"
                >
                  {buying ? 'PROCESANDO...' : 'ADQUIRIR PAQUETE'}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Modal Transferencia / Alias */}
      <AnimatePresence>
        {aliasModalInfo && currentServicio && currentRegla && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-7 shadow-2xl space-y-5"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-neutral-900">Datos para Transferencia</h3>
                <button onClick={() => setAliasModalInfo(null)} className="p-1 text-neutral-400 hover:text-neutral-700">
                  <X size={20} />
                </button>
              </div>

              <div className="p-4 rounded-2xl bg-primary-light/60 border border-primary-main/20 text-center">
                <p className="text-xs font-bold uppercase tracking-wider text-neutral-500">
                  {currentRegla.cantidad_sesiones} sesión(es) • {currentServicio.nombre}
                </p>
                <p className="text-2xl font-black text-primary-main mt-1">
                  ${totalCalculado.toLocaleString('es-AR')}
                </p>
              </div>

              <div className="space-y-3 bg-neutral-50 p-4 rounded-2xl border border-neutral-100 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <p className="text-[11px] font-bold uppercase text-neutral-400">Alias / CVU</p>
                    <p className="font-bold text-neutral-900 select-all">
                      {aliasModalInfo.alias || 'Consultar por WhatsApp'}
                    </p>
                  </div>
                  {aliasModalInfo.alias && (
                    <button
                      onClick={() => handleCopyAlias(aliasModalInfo.alias)}
                      className="p-2 rounded-xl bg-white border border-neutral-200 text-neutral-600 hover:text-primary-main"
                      title="Copiar Alias"
                    >
                      {copiedAlias ? <Check size={16} className="text-emerald-600" /> : <Copy size={16} />}
                    </button>
                  )}
                </div>

                {aliasModalInfo.cbu && (
                  <div>
                    <p className="text-[11px] font-bold uppercase text-neutral-400">CBU</p>
                    <p className="font-medium text-neutral-800 select-all">{aliasModalInfo.cbu}</p>
                  </div>
                )}

                {aliasModalInfo.titular && (
                  <div>
                    <p className="text-[11px] font-bold uppercase text-neutral-400">Titular</p>
                    <p className="font-medium text-neutral-800">{aliasModalInfo.titular}</p>
                  </div>
                )}
              </div>

              <p className="text-xs text-neutral-500 leading-relaxed">
                Una vez realizada la transferencia, envianos el comprobante por WhatsApp para acreditar tus sesiones inmediatamente en tu billetera.
              </p>

              <div className="flex gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => setAliasModalInfo(null)}
                  className="flex-1 py-3 rounded-xl border border-neutral-200 text-xs font-bold text-neutral-600 hover:bg-neutral-50"
                >
                  Cerrar
                </button>
                <button
                  type="button"
                  onClick={handleWhatsAppComprobante}
                  className="flex-1 py-3 px-4 rounded-xl bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 flex items-center justify-center gap-1.5"
                >
                  <MessageCircle size={15} /> Enviar Comprobante
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
