import React, { useMemo } from 'react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import { type Turno } from '../../hooks/useBookings'
import { AlertTriangle } from 'lucide-react'

interface CancelModalProps {
  isOpen: boolean
  onClose: () => void
  turno: Turno | null
  onConfirm: (turnoId: string) => void
}

export function CancelModal({ isOpen, onClose, turno, onConfirm }: CancelModalProps) {
  const isLateCancellation = useMemo(() => {
    if (!turno) return false
    const [year, month, day] = turno.date.split('-').map(Number)
    const [hours, minutes] = turno.time.split(':').map(Number)
    const turnoDate = new Date(year, month - 1, day, hours, minutes)
    const now = new Date()
    const diffHours = (turnoDate.getTime() - now.getTime()) / (1000 * 60 * 60)
    return diffHours < 24
  }, [turno])

  if (!turno) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Cancelar Reserva">
      <div className="space-y-6">
        <p className="text-muted text-sm">
          Estás a punto de cancelar tu clase de <strong>{turno.classType}</strong> del día {turno.date} a las {turno.time}.
        </p>

        {isLateCancellation && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3 text-red-800">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-600" />
            <div>
              <p className="font-semibold text-sm">Cancelación Tardía</p>
              <p className="text-sm mt-1">
                Estás cancelando con menos de 24 horas de anticipación. Según nuestra política, perderás el crédito de esta clase y no será devuelto a tu plan.
              </p>
            </div>
          </div>
        )}

        <div className="flex gap-3 justify-end mt-4">
          <Button onClick={onClose} variant="outline" className="w-full">Atrás</Button>
          <Button onClick={() => onConfirm(turno.id)} variant="destructive" className="w-full">
            Sí, cancelar clase
          </Button>
        </div>
      </div>
    </Modal>
  )
}
