/* Developed by FireSeed - Fueling Innovation */
import React from 'react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import { type Turno } from '../../hooks/useBookings'

interface BookingModalProps {
  isOpen: boolean
  onClose: () => void
  turno: Turno | null
  onConfirm: (turnoId: string, isRecurring: boolean) => void
}

export function BookingModal({ isOpen, onClose, turno, onConfirm }: BookingModalProps) {
  const [cachedTurno, setCachedTurno] = React.useState<Turno | null>(turno)
  
  React.useEffect(() => {
    if (turno) setCachedTurno(turno)
  }, [turno])

  const displayTurno = turno || cachedTurno
  if (!displayTurno) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirmar Reserva">
      <div className="space-y-6">
        <div className="rounded-lg bg-violett-50 p-4">
          <p className="text-sm text-violett-700 font-semibold mb-1">{displayTurno.date} - {displayTurno.time}</p>
          <p className="text-lg font-bold text-violett-900">{displayTurno.classType}</p>
        </div>
        
                <p className="text-muted text-sm">
          {displayTurno.allowsRecurring 
            ? '¿Cómo te gustaría reservar este turno? Puedes anotarte solo para este día, o fijar este horario todas las semanas.' 
            : 'Esta clase es puntual. Solo puedes reservar para esta fecha específica.'}
        </p>

        <div className="flex flex-col gap-3">
          <Button onClick={() => onConfirm(displayTurno.id, false)} className="w-full">
            Reserva Puntual (Solo esta clase)
          </Button>
          {displayTurno.allowsRecurring && (
            <Button onClick={() => onConfirm(displayTurno.id, true)} variant="outline" className="w-full">
              Reserva Recurrente (Fijo semanal)
            </Button>
          )}
        </div>
      </div>
    </Modal>
  )
}
