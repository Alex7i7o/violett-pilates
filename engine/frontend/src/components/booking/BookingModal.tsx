/* Developed by FireSeed - Fueling Innovation */
import React from 'react'
import { Modal } from '../ui/Modal'
import { FeedbackButton } from '../ui/FeedbackButton'
import { type Turno } from '../../hooks/useBookings'

interface BookingModalProps {
  isOpen: boolean
  onClose: () => void
  turno: Turno | null
  onConfirm: (turnoId: string, isRecurring: boolean) => Promise<void> | void
}

export function BookingModal({ isOpen, onClose, turno, onConfirm }: BookingModalProps) {
  const [cachedTurno, setCachedTurno] = React.useState<Turno | null>(turno)
  
  React.useEffect(() => {
    if (turno) setCachedTurno(turno)
  }, [turno])

  const displayTurno = turno || cachedTurno

  const handleConfirm = async (isRecurring: boolean) => {
    if (!displayTurno) return
    try {
      await onConfirm(displayTurno.id, isRecurring)
      onClose()
    } catch (err: any) {
      // onConfirm already shows a toast with the error (e.g. "Ya tienes una reserva")
      // so we just close the modal gracefully without crashing
      onClose()
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirmar Reserva">
      {displayTurno ? (
      <div className="space-y-6">
        <div className="rounded-lg bg-primary-light/50 p-4">
          <p className="text-sm text-primary-hover font-semibold mb-1">{displayTurno.date} - {displayTurno.time}</p>
          <p className="text-lg font-bold text-primary-main">{displayTurno.classType}</p>
        </div>
        
        <p className="text-muted text-sm">
          {displayTurno.allowsRecurring 
            ? 'Como te gustaria reservar este turno? Puedes anotarte solo para este dia, o fijar este horario todas las semanas.' 
            : 'Esta clase es puntual. Solo puedes reservar para esta fecha especifica.'}
        </p>

        <div className="flex flex-col gap-3">
          <FeedbackButton
            onClick={() => handleConfirm(false)}
            className="w-full"
            initialText="Reserva Puntual (Solo esta clase)"
            successText="Reservada!"
          />
          {displayTurno.allowsRecurring && (
            <FeedbackButton
              onClick={() => handleConfirm(true)}
              variant="outline"
              className="w-full"
              initialText="Reserva Recurrente (Fijo semanal)"
              successText="Reservada!"
            />
          )}
        </div>
      </div>
      ) : null}
    </Modal>
  )
}
