import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { WalletCards, Clock, CheckCircle } from 'lucide-react';

export const ClientDashboard = () => {
  const [billeteras, setBilleteras] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/billeteras/')
      .then(res => setBilleteras(res.data))
      .catch(() => toast.error('Error cargando billetera'))
      .finally(() => setLoading(false));
  }, []);

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
      <div className="w-full space-y-4">
        {[1,2,3].map(i => (
          <div key={i} className="h-32 bg-neutral-200 rounded-[2rem] animate-pulse"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="w-full pb-20">
      <div className="flex items-center gap-3 mb-8 px-2">
        <div className="p-2.5 bg-primary-50 text-primary-main rounded-xl">
          <WalletCards size={24} />
        </div>
        <h1 className="text-2xl font-bold text-neutral-900 tracking-tight">Mi Billetera</h1>
      </div>

      {billeteras.length === 0 ? (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-neutral-50 rounded-[2rem] p-8 text-center border-2 border-dashed border-neutral-200">
          <p className="text-neutral-500 font-medium">No tienes paquetes activos.</p>
        </motion.div>
      ) : (
        <motion.div 
          variants={containerVariants} 
          initial="hidden" 
          animate="show"
          className="grid gap-4 sm:grid-cols-2"
        >
          {billeteras.map(bill => {
            const isAgotado = bill.estado === 'AGOTADO';
            const isVencido = bill.estado === 'VENCIDO';
            const isInactive = isAgotado || isVencido;
            const progress = (bill.sesiones_restantes / bill.sesiones_totales) * 100;

            return (
              <motion.div 
                variants={itemVariants}
                key={bill.id} 
                className={`p-6 rounded-[2rem] relative overflow-hidden transition-all ${isInactive ? 'bg-neutral-100/50 text-neutral-400 border border-neutral-100' : 'bg-white shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-neutral-100 text-neutral-900'}`}
              >
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className={`font-bold text-lg leading-tight mb-1 ${isInactive ? 'text-neutral-500' : 'text-neutral-900'}`}>{bill.servicio_detalle?.nombre || 'Servicio'}</h3>
                    <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider">
                      {isVencido ? (
                        <span className="text-red-500 flex items-center gap-1"><Clock size={12}/> Vencido</span>
                      ) : isAgotado ? (
                        <span className="text-orange-500 flex items-center gap-1"><CheckCircle size={12}/> Agotado</span>
                      ) : (
                        <span className="text-green-500 flex items-center gap-1"><CheckCircle size={12}/> Activo</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <div className="flex justify-between text-sm mb-2 font-medium">
                    <span className={isInactive ? 'text-neutral-400' : 'text-neutral-600'}><strong className={`text-lg ${isInactive ? '' : 'text-primary-main'}`}>{bill.sesiones_restantes}</strong> restantes</span>
                    <span className="text-neutral-400 self-end mb-0.5">de {bill.sesiones_totales} totales</span>
                  </div>
                  <div className="w-full bg-neutral-100 rounded-full h-2.5 overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 1, ease: [0.23, 1, 0.32, 1] }}
                      className={`h-full rounded-full ${isInactive ? 'bg-neutral-300' : 'bg-primary-main'}`} 
                    />
                  </div>
                </div>

                <div className="flex justify-between text-[11px] font-medium text-neutral-400 bg-neutral-50 p-3 rounded-xl">
                  <div>
                    <p className="uppercase tracking-wider text-[9px] mb-0.5 opacity-70">Compra</p>
                    <p>{bill.fecha_compra}</p>
                  </div>
                  <div className="text-right">
                    <p className="uppercase tracking-wider text-[9px] mb-0.5 opacity-70">Vence</p>
                    <p>{bill.fecha_vencimiento}</p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
};
