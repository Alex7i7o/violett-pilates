/* Developed by FireSeed - Fueling Innovation */
import { motion, AnimatePresence } from 'framer-motion';
import React, { useState } from 'react'
import { toast } from 'sonner';
import { ConfirmModal } from '../components/ui/ConfirmModal';
import { useClientProfile } from '../hooks/useClientProfile'

import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { BookingGrid } from '../components/booking/BookingGrid'
import { CancelModal } from '../components/booking/CancelModal'
import { ClientProfileHeader } from '../components/dashboard/ClientProfileHeader'
import { ClientRecurringClasses } from '../components/dashboard/ClientRecurringClasses'
import { ClientUpcomingClasses } from '../components/dashboard/ClientUpcomingClasses'
import { ReviewForm } from '../components/ui/ReviewForm'
import { useBookings, type Turno } from '../hooks/useBookings'
import { api } from '../lib/api'



export function Dashboard() {
  const { profile, loading: profileLoading, refetch: refetchProfile } = useClientProfile()
  const { turnos, loading: bookingsLoading, bookTurno, cancelTurno, refetch: refetchTurnos } = useBookings()
  const [selectedTurnoToCancel, setSelectedTurnoToCancel] = useState<Turno | null>(null)
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


  const handleBook = async (id: string, recurring: boolean) => {
    await bookTurno(id, recurring)
    refetchProfile()
  }

  const handleCancel = async (id: string) => {
    await cancelTurno(id)
    refetchProfile()
    setSelectedTurnoToCancel(null)
  }

  const handleCancelRecurrencia = async (id: string) => {
    try {
      await api.post('/recurrencias/cancel/', { id })
      refetchProfile()
      refetchTurnos()
      toast.success("Horario fijo cancelado exitosamente.");
    } catch (err: any) {
      toast.error("Error al cancelar el horario fijo.")
    }
  }

  const promptCancelRecurrencia = (id: string) => {
    setRecurrenciaToCancel(id);
  }



  

    return (
    <AnimatePresence mode="wait">
      {(profileLoading || bookingsLoading) ? (
        <motion.div 
          key="skeleton"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="min-h-screen flex items-center justify-center"
        >
          {/* Skeleton representation of dashboard */}
          <div className="w-full max-w-5xl mx-auto space-y-8 p-4">
            <div className="h-32 bg-violett-100 rounded-2xl animate-pulse"></div>
            <div className="h-64 bg-violett-50 rounded-2xl animate-pulse"></div>
            <div className="h-64 bg-violett-50 rounded-2xl animate-pulse"></div>
          </div>
        </motion.div>
      ) : !profile ? null : (
        <motion.div 
          key="content"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className="max-w-5xl mx-auto space-y-8"
        >
          <ClientProfileHeader profile={profile} />

      <ClientRecurringClasses recurrencias={profile.recurrencias} onCancelClick={promptCancelRecurrencia} />

      <ClientUpcomingClasses turnos={turnos} onCancelClick={setSelectedTurnoToCancel} />

      {/* Grilla de Reservas */}
      <div className="pt-4 border-t border-violett-100">
        <div className="flex justify-end mb-4">
          <Button variant="outline" size="sm" onClick={toggleHistory}>
            {showHistory ? "Ver Agenda Disponible" : "Ver clases a las que asistí"}
          </Button>
        </div>
        {!showHistory ? (
        <BookingGrid 
          turnos={turnos}
          loading={bookingsLoading}
          onBook={handleBook}
          onCancel={handleCancel}
        />
        ) : (
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
                         <p className="text-violett-900 font-medium">{h.clase_nombre}</p>
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

      {/* Reseñas */}
      <ReviewForm />

      <CancelModal 
        isOpen={!!selectedTurnoToCancel}
        onClose={() => setSelectedTurnoToCancel(null)}
        turno={selectedTurnoToCancel}
        onConfirm={handleCancel}
      />

      <ConfirmModal
        isOpen={!!recurrenciaToCancel}
        onClose={() => setRecurrenciaToCancel(null)}
        onConfirm={() => {
          if (recurrenciaToCancel) handleCancelRecurrencia(recurrenciaToCancel);
        }}
        title="Cancelar Horario Fijo"
        message="¿Estás seguro de cancelar tu horario fijo permanentemente?

Esto cancelará todas tus reservas futuras para este horario."
        confirmText="Sí, cancelar"
        cancelText="Mantener horario"
        isDestructive={true}
      />
        </motion.div>
      )}
    </AnimatePresence>
  )
}
