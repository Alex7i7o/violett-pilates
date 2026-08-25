import os

button_code = '''import * as React from "react"
import { cn } from "../../lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost' | 'link' | 'destructive'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    
    const variants = {
      default: "bg-violett-900 text-white hover:bg-violett-800 shadow-soft",
      destructive: "bg-red-500 text-white hover:bg-red-600 shadow-soft",
      outline: "border border-violett-200 bg-transparent hover:bg-violett-50 text-violett-900",
      ghost: "hover:bg-violett-50 text-violett-900",
      link: "text-violett-600 underline-offset-4 hover:underline",
    }
    
    const sizes = {
      default: "h-10 px-4 py-2",
      sm: "h-9 rounded-md px-3",
      lg: "h-11 rounded-md px-8 text-lg",
      icon: "h-10 w-10",
    }

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium ring-offset-background transition-[transform,background-color,border-color,color] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violett-500 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
'''

modal_code = '''import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X } from "lucide-react"
import { cn } from "../../lib/utils"

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  className?: string
}

export function Modal({ isOpen, onClose, title, children, className }: ModalProps) {
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => { document.body.style.overflow = 'unset' }
  }, [isOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.25, ease: "easeOut" } }}
            exit={{ opacity: 0, transition: { duration: 0.15, ease: "linear" } }}
            className="fixed inset-0 bg-violett-900/40 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ 
              opacity: 1, 
              scale: 1, 
              y: 0, 
              transition: { type: "spring", duration: 0.25, bounce: 0.15 } 
            }}
            exit={{ 
              opacity: 0, 
              scale: 0.95, 
              y: 10, 
              transition: { duration: 0.15, ease: "easeOut" } 
            }}
            className={cn(
              "relative z-50 w-full max-w-lg overflow-hidden rounded-2xl bg-card shadow-glass sm:w-[90%]",
              className
            )}
          >
            <div className="flex items-center justify-between border-b border-violett-100 px-6 py-4">
              {title && <h2 className="text-xl font-semibold text-foreground">{title}</h2>}
              <button
                onClick={onClose}
                className="rounded-full p-2 text-muted transition-colors hover:bg-violett-50 hover:text-foreground active:scale-95"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              {children}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
'''

cancel_modal_code = '''import React from 'react'
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
          <Button onClick={() => onConfirm(turno.id)} variant="destructive">
            Sí, cancelar clase
          </Button>
        </div>
      </div>
    </Modal>
  )
}
'''

with open('frontend/src/components/ui/Button.tsx', 'w', encoding='utf-8') as f:
    f.write(button_code)
with open('frontend/src/components/ui/Modal.tsx', 'w', encoding='utf-8') as f:
    f.write(modal_code)
with open('frontend/src/components/booking/CancelModal.tsx', 'w', encoding='utf-8') as f:
    f.write(cancel_modal_code)

print("Files fixed successfully")
