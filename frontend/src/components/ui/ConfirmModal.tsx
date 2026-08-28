import React from 'react'
import { Modal } from './Modal'
import { Button } from './Button'
import { FeedbackButton } from './FeedbackButton'
import { haptics } from '../../lib/haptics';


interface ConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => Promise<void> | void
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
  React.useEffect(() => {
    if (isOpen) {
      if (isDestructive) {
        haptics.warning();
      } else {
        haptics.light();
      }
    }
  }, [isOpen, isDestructive]);


  React.useEffect(() => {
    if (isOpen) {
      if (isDestructive) {
        haptics.warning();
      } else {
        haptics.light();
      }
    }
  }, [isOpen, isDestructive]);

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
