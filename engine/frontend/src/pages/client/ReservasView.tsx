import React, { useState } from 'react';
import { useClientProfile } from '../../hooks/useClientProfile';
import { useBookings, type Turno } from '../../hooks/useBookings';
import { ClientUpcomingClasses } from '../../components/dashboard/ClientUpcomingClasses';
import { ClientRecurringClasses } from '../../components/dashboard/ClientRecurringClasses';
import { CancelModal } from '../../components/booking/CancelModal';
import { ConfirmModal } from '../../components/ui/ConfirmModal';
import { ReviewForm } from '../../components/ui/ReviewForm';
import { Button } from '../../components/ui/Button';
import { Card, CardContent } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { api } from '../../lib/api';
import { toast } from 'sonner';

export function ReservasView() {
  const { profile, refetch: refetchProfile } = useClientProfile();
  const { turnos, cancelTurno, refetch: refetchTurnos } = useBookings();

  const [selectedTurnoToCancel, setSelectedTurnoToCancel] = useState<Turno | null>(null);
  const [recurrenciaToCancel, setRecurrenciaToCancel] = useState<string | null>(null);

    const [showHistory, setShowHistory] = useState(false);
  const [historial, setHistorial] = useState<any[]>([]);
  const [historialLoading, setHistorialLoading] = useState(false);

  const fetchHistorial = async () => {
    if (historial.length > 0) return;
    try {
      setHistorialLoading(true);
      const res = await api.get('/reservas/historial/');
      setHistorial(res.data);
    } catch (e) {
      toast.error('Error cargando historial');
    } finally {
      setHistorialLoading(false);
    }
  };

  const toggleHistory = () => {
    if (!showHistory) fetchHistorial();
    setShowHistory(!showHistory);
  };

  const upcomingBookings = turnos.filter(t => t.isBookedByMe);

  const handleCancelConfirm = async (turnoId: string) => {
    await cancelTurno(turnoId);
    setSelectedTurnoToCancel(null);
  };

  const handleCancelRecurrencia = async (id: string) => {
    try {
      await api.post('/recurrencias/cancel/', { id });
      toast.success('Baja definitiva confirmada.');
      setRecurrenciaToCancel(null);
      refetchProfile();
      refetchTurnos();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Error al cancelar la reserva recurrente.');
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 md:px-0 pt-4 md:pt-0 pb-6 space-y-8">
      <div className="md:hidden mt-2 mb-2">
        <h1 className="text-3xl font-bold text-foreground">Mis Reservas</h1>
      </div>

      <ClientUpcomingClasses 
        turnos={upcomingBookings}
        onCancelClick={setSelectedTurnoToCancel}
      />
      
      <ClientRecurringClasses 
        recurrencias={profile?.recurrencias || []}
        onCancelClick={setRecurrenciaToCancel}
      />

      <div className="pt-4 border-t border-primary-light">
        <div className="flex justify-end mb-4">
          <Button variant="outline" size="sm" onClick={toggleHistory}>
            {showHistory ? "Ver próximas reservas" : "Ver clases a las que asistí"}
          </Button>
        </div>
        
        {showHistory && (
          <div className="space-y-4">
            {historialLoading ? (
               <div className="text-center text-muted py-8">Cargando historial...</div>
            ) : historial.length === 0 ? (
               <div className="text-center text-muted py-8">No has asistido a clases este mes aún.</div>
            ) : (
               <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                 {historial.map((h: any) => (
                   <Card key={h.id} className="opacity-80 relative overflow-hidden bg-gray-50/50">
                     <CardContent className="p-4">
                       <p className="font-bold text-foreground text-lg">{h.fecha}</p>
                       <p className="text-sm text-muted mb-2">{h.hora_inicio} - {h.hora_fin}</p>
                       <div className="flex justify-between items-end">
                         <p className="text-primary-main font-medium">{h.clase_nombre}</p>
                         <Badge variant="secondary" className="bg-gray-100 text-gray-700">{h.estado_reserva}</Badge>
                       </div>
                     </CardContent>
                   </Card>
                 ))}
               </div>
            )}
          </div>
        )}
      </div>
      
      <ReviewForm />

      <CancelModal
        isOpen={!!selectedTurnoToCancel}
        onClose={() => setSelectedTurnoToCancel(null)}
        turno={selectedTurnoToCancel}
        onConfirm={handleCancelConfirm}
      />

      <ConfirmModal
        isOpen={!!recurrenciaToCancel}
        onClose={() => setRecurrenciaToCancel(null)}
        onConfirm={() => {
          if (recurrenciaToCancel) {
            handleCancelRecurrencia(recurrenciaToCancel);
          }
        }}
        title="Baja definitiva"
        message="¿Estás segura de que quieres darte de baja definitiva de este horario fijo semanal? Perderás tu lugar y otras personas podrán ocuparlo."
        confirmText="Sí, dar de baja"
      />
    </div>
  );
}
