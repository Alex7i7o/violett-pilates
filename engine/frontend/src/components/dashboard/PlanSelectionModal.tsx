import React, { useEffect, useState } from 'react';
import { Modal } from '../ui/Modal';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { api } from '../../lib/api';
import { toast } from 'sonner';
import { useClientConfig } from '../../context/ClientConfigContext';

interface Plan {
  id: string;
  nombre: string;
  descripcion: string;
  precio: number;
  clases_incluidas: number;
  duracion_dias: number;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  currentPlan?: string;
}

export function PlanSelectionModal({ isOpen, onClose, currentPlan }: Props) {
  const [planes, setPlanes] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [aliasInfo, setAliasInfo] = useState<any>(null);
  const config = useClientConfig();

  useEffect(() => {
    if (isOpen) {
      api.get<Plan[]>('/admin/planes/')
        .then(res => {
          setPlanes(res.data);
          setLoading(false);
        })
        .catch(() => {
          toast.error("Error al cargar los planes");
          setLoading(false);
        });
    } else {
      setSelectedPlan(null);
      setAliasInfo(null);
    }
  }, [isOpen]);

  const handleCheckout = async (plan: Plan) => {
    setProcessing(true);
    try {
      const res = await api.post('/pagos/checkout/', { plan_id: plan.id });
      if (res.data.type === 'mercadopago') {
        window.location.href = res.data.init_point;
      } else if (res.data.type === 'alias') {
        setSelectedPlan(plan);
        setAliasInfo(res.data.info);
      }
    } catch (error) {
      toast.error("Error al procesar el pago");
    } finally {
      setProcessing(false);
    }
  };

  const handleWhatsAppRedirect = () => {
    if (!selectedPlan || !aliasInfo) return;
    const phoneNumber = config.contact_phone || "5491164142172"; // 1164142172 Violett
    const message = `Hola! Ya realicé la transferencia para adquirir el plan *${selectedPlan.nombre}* por $${Number(selectedPlan.precio).toLocaleString('es-AR')}. Te adjunto el comprobante:`;
    window.open(`https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`, '_blank');
    onClose();
  };


  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Adquirir o Renovar Plan">
      {loading ? (
        <div className="p-8 text-center text-gray-500">Cargando planes disponibles...</div>
      ) : !selectedPlan ? (
        <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
          {planes.map(plan => (
            <Card key={plan.id} className="cursor-pointer hover:border-primary-main transition-colors" onClick={() => handleCheckout(plan)}>
              <CardHeader className="pb-2">
                <CardTitle className="text-xl text-primary-main">{plan.nombre}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-end">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">{plan.clases_incluidas} clases / {plan.duracion_dias} días</p>
                    <p className="text-2xl font-bold text-primary-hover">${Number(plan.precio).toLocaleString('es-AR')}</p>
                  </div>
                  <Button variant="outline" size="sm" disabled={processing}>
                    {processing ? "Procesando..." : "Seleccionar"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-primary-light/50 p-4 rounded-xl border border-primary-light text-center">
            <h3 className="text-lg font-bold text-primary-main mb-2">Elegiste: {selectedPlan.nombre}</h3>
            <p className="text-2xl font-black text-primary-hover mb-4">${Number(selectedPlan.precio).toLocaleString('es-AR')}</p>
            
            <div className="bg-white p-4 rounded-lg shadow-sm text-left mb-4">
              <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Datos para Transferencia</p>
              <p className="font-medium">CVU / ALIAS:</p>
              <p className="text-lg font-bold text-primary-main select-all">{aliasInfo.alias}</p>
              {aliasInfo.cbu && (
                <>
                  <p className="font-medium mt-2">CBU:</p>
                  <p className="text-gray-700 select-all">{aliasInfo.cbu}</p>
                </>
              )}
              <p className="font-medium mt-2">Titular:</p>
              <p className="text-gray-700">{aliasInfo.titular}</p>
            </div>
            
            <div className="text-sm text-gray-600 space-y-2">
              <p>1. Realiza la transferencia desde tu homebanking o billetera virtual.</p>
              <p>2. Guarda una captura de pantalla del comprobante.</p>
              <p>3. Presiona el botón de abajo para enviarnos el comprobante por WhatsApp.</p>
            </div>
          </div>
          
          <div className="flex gap-4">
            <Button variant="outline" className="flex-1" onClick={() => setSelectedPlan(null)}>Volver</Button>
            <Button className="flex-1 bg-green-600 hover:bg-green-700 text-white" onClick={handleWhatsAppRedirect}>
              Ya pagué (Enviar WhatsApp)
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
