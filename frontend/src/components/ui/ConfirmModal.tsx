import React from 'react'
import { Modal } from './Modal'
import { Button } from './Button'

interface ConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  isDestructive?: boolean
}

export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirmar acci\u00f3n',
  message,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  isDestructive = false
}: ConfirmModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <p className="text-muted mb-6 whitespace-pre-wrap">{message}</p>
      <div className="flex gap-4">
        <Button variant="outline" className="w-full" onClick={onClose}>
          {cancelText}
        </Button>
        <Button
          variant={isDestructive ? 'destructive' : 'default'}
          className="w-full"
          onClick={() => {
            onConfirm()
            onClose()
          }}
        >
          {confirmText}
        </Button>
      </div>
    </Modal>
  )
}
