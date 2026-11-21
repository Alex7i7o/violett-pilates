import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useClientConfig } from '@/context/ClientConfigContext';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Badge,
  Button,
  Modal,
  haptics
} from 'fireseed-ui';
import { ShoppingBag, Tag, ChevronDown, Copy, Check, MessageCircle } from 'lucide-react';

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
        <div className="h-40 bg-white rounded-2xl border border-neutral-100 shadow-soft animate-pulse"></div>
        <div className="h-24 bg-white rounded-2xl border border-neutral-100 shadow-soft animate-pulse"></div>
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
        <motion.div variants={itemVariants}>
          <div className="bg-white border border-neutral-100 shadow-soft p-6 sm:p-8 rounded-2xl space-y-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-[#F9F6ED] border border-[#C5A059]/30 text-[#C5A059] rounded-2xl shadow-xs">
                <ShoppingBag size={24} />
              </div>
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-[#34236F] font-serif tracking-tight">
                  Tienda de Paquetes
                </h2>
                <p className="text-xs sm:text-sm text-neutral-500 mt-0.5">
                  Seleccioná un tratamiento estético y la cantidad de sesiones con descuento.
                </p>
              </div>
            </div>

            <div className="space-y-5">
              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#34236F] ml-1">
                  Tratamiento
                </label>
                <div className="relative">
                  <select
                    value={selectedServicio}
                    onChange={e => {
                      haptics.selection();
                      setSelectedServicio(e.target.value);
                    }}
                    className="w-full p-4 pl-5 pr-12 rounded-xl border border-neutral-200 bg-white outline-none focus:border-[#C5A059] transition-all appearance-none text-[#34236F] font-medium text-sm"
                  >
                    {servicios.map(s => (
                      <option key={s.id} value={s.id} className="text-[#34236F]">
                        {s.nombre} (${parseFloat(s.precio_base).toLocaleString('es-AR')} por sesión)
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-[#C5A059] pointer-events-none" size={18} />
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#34236F] ml-1">
                  Cantidad de Sesiones
                </label>
                <div className="relative">
                  <select
                    value={selectedRegla}
                    onChange={e => {
                      haptics.selection();
                      setSelectedRegla(e.target.value);
                    }}
                    className="w-full p-4 pl-5 pr-12 rounded-xl border border-neutral-200 bg-white outline-none focus:border-[#C5A059] transition-all appearance-none text-[#34236F] font-medium text-sm"
                  >
                    {reglas.map(r => (
                      <option key={r.id} value={r.id} className="text-[#34236F]">
                        {r.cantidad_sesiones} Sesión{r.cantidad_sesiones > 1 ? 'es' : ''}
                        {parseFloat(r.descuento_porcentaje) > 0 ? ` (${parseFloat(r.descuento_porcentaje)}% OFF)` : ''}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 text-[#C5A059] pointer-events-none" size={18} />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Floating Checkout Bar */}
      <AnimatePresence>
        {currentServicio && currentRegla && (
          <motion.div
            initial={{ opacity: 0, y: 80 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 80 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed bottom-[4.5rem] sm:bottom-8 left-0 right-0 z-40 px-4 sm:px-0 pointer-events-none"
          >
            <div className="max-w-4xl mx-auto flex justify-center">
              <div className="bg-[#34236F] text-white rounded-full shadow-2xl p-2 pl-6 pr-2 flex items-center justify-between w-full max-w-[95%] sm:max-w-md pointer-events-auto border border-[#C5A059]/30">
                <div className="flex flex-col mr-4">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-white/70">Total a abonar</span>
                  <div className="flex items-center gap-2">
                    <span className="text-lg sm:text-xl font-bold font-mono text-[#C5A059]">
                      ${totalCalculado.toLocaleString('es-AR')}
                    </span>
                    {porcentajeDescuento > 0 && (
                      <Badge variant="glow" size="sm" className="!text-[10px]">
                        <Tag size={10} className="mr-0.5" /> {porcentajeDescuento}% OFF
                      </Badge>
                    )}
                  </div>
                </div>

                <Button
                  variant="glow"
                  size="md"
                  onClick={() => {
                    haptics.impact();
                    handleBuy();
                  }}
                  disabled={buying}
                  className="!bg-[#C5A059] hover:!bg-[#B38E4C] !text-white font-bold text-xs rounded-full px-5 py-3 whitespace-nowrap shadow-md shadow-[#C5A059]/30"
                >
                  {buying ? 'PROCESANDO...' : 'ADQUIRIR PAQUETE'}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Modal Transferencia / Alias */}
      <Modal
        isOpen={Boolean(aliasModalInfo && currentServicio && currentRegla)}
        onClose={() => setAliasModalInfo(null)}
        title="Datos para Transferencia Bancaria"
        description="Acreditación instantánea tras enviar el comprobante"
        className="bg-white border border-neutral-200 text-[#34236F]"
      >
        {aliasModalInfo && currentServicio && currentRegla && (
          <div className="space-y-5">
            <div className="p-4 rounded-xl bg-[#F9F6ED] border border-[#C5A059]/30 text-center">
              <p className="text-xs font-semibold uppercase tracking-wider text-neutral-600">
                {currentRegla.cantidad_sesiones} sesión(es) • {currentServicio.nombre}
              </p>
              <p className="text-2xl font-bold text-[#C5A059] font-mono mt-1">
                ${totalCalculado.toLocaleString('es-AR')}
              </p>
            </div>

            <div className="space-y-3 bg-neutral-50 p-4 rounded-xl border border-neutral-200 text-xs sm:text-sm">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-[#C5A059]">Alias / CVU</p>
                  <p className="font-mono font-bold text-[#34236F] select-all mt-0.5">
                    {aliasModalInfo.alias || 'Consultar por WhatsApp'}
                  </p>
                </div>
                {aliasModalInfo.alias && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCopyAlias(aliasModalInfo.alias)}
                    className="border-neutral-200 text-neutral-600 hover:text-[#34236F] hover:bg-white"
                    title="Copiar Alias"
                  >
                    {copiedAlias ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
                  </Button>
                )}
              </div>

              {aliasModalInfo.cbu && (
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-[#C5A059]">CBU</p>
                  <p className="font-mono text-neutral-700 select-all mt-0.5">{aliasModalInfo.cbu}</p>
                </div>
              )}

              {aliasModalInfo.titular && (
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-[#C5A059]">Titular de la cuenta</p>
                  <p className="text-[#34236F] font-medium mt-0.5">{aliasModalInfo.titular}</p>
                </div>
              )}
            </div>

            <p className="text-xs text-neutral-500 leading-relaxed">
              Una vez realizada la transferencia, envianos el comprobante por WhatsApp para acreditar tus sesiones inmediatamente en tu billetera.
            </p>

            <div className="flex gap-3 pt-2 border-t border-neutral-100">
              <Button
                variant="outline"
                size="md"
                onClick={() => setAliasModalInfo(null)}
                className="flex-1 text-xs border-neutral-200 text-neutral-600 rounded-xl"
              >
                Cerrar
              </Button>
              <Button
                variant="glow"
                size="md"
                onClick={handleWhatsAppComprobante}
                className="flex-1 text-xs !bg-emerald-600 hover:!bg-emerald-500 !text-white font-bold rounded-xl"
              >
                <MessageCircle size={15} className="mr-1.5" /> Enviar Comprobante
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};