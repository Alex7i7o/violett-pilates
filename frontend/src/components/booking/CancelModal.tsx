/* Developed by FireSeed - Fueling Innovation */
import React from 'react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import { type Turno } from '../../hooks/useBookings'

interface CancelModalProps {
  isOpen: boolean
  onClose: () => void
  turno: Turno | null
  onConfirm: (turnoId: string) => void
}

export function CancelModal({ isOpen, onClose, turno, onConfirm }: CancelModalProps) {
  if (!turno) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Cancelar Reserva">
      <div className="space-y-6">
        <p className="text-muted text-sm">
          Estás a punto de cancelar tu clase de <strong>{turno.classType}</strong> del día {turno.date} a las {turno.time}.
        </p>

        <div className="flex gap-3 justify-end mt-4">
          <Button onClick={onClose} variant="ghost">Atrás</Button>
          <Button onClick={() => onConfirm(turno.id)} className="bg-red-600 hover:bg-red-700">
            Sí, cancelar clase
          </Button>
        </div>
      </div>
    </Modal>
  )
}
