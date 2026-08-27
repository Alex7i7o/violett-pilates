import React, { useEffect, useState } from 'react';
import { Modal } from '../ui/Modal';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { api } from '../../lib/api';
import { toast } from 'sonner';

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
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);

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
    }
  }, [isOpen]);

  const handleWhatsAppRedirect = () => {
    if (!selectedPlan) return;
    const phoneNumber = "5491123456789"; // Cambiar por el real
    const message = `Hola Violett Pilates! Ya realicé la transferencia para adquirir el plan *${selectedPlan.nombre}* por $${selectedPlan.precio}. Te adjunto el comprobante:`;
    window.open(`https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`, '_blank');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Adquirir o Renovar Plan">
      {loading ? (
        <div className="p-8 text-center text-gray-500">Cargando planes disponibles...</div>
      ) : !selectedPlan ? (
        <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
          {planes.map(plan => (
            <Card key={plan.id} className="cursor-pointer hover:border-violett-500 transition-colors" onClick={() => setSelectedPlan(plan)}>
              <CardHeader className="pb-2">
                <CardTitle className="text-xl text-violett-900">{plan.nombre}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-end">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">{plan.clases_incluidas} clases / {plan.duracion_dias} días</p>
                    <p className="text-2xl font-bold text-violett-700">${plan.precio}</p>
                  </div>
                  <Button variant="outline" size="sm">Seleccionar</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-violett-50 p-4 rounded-xl border border-violett-100 text-center">
            <h3 className="text-lg font-bold text-violett-900 mb-2">Elegiste: {selectedPlan.nombre}</h3>
            <p className="text-2xl font-black text-violett-700 mb-4">${selectedPlan.precio}</p>
            
            <div className="bg-white p-4 rounded-lg shadow-sm text-left mb-4">
              <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Datos para Transferencia</p>
              <p className="font-medium">CVU / ALIAS:</p>
              <p className="text-lg font-bold text-violett-900 select-all">violett.pilates.mp</p>
              <p className="font-medium mt-2">Titular:</p>
              <p className="text-gray-700">Violett Pilates</p>
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
