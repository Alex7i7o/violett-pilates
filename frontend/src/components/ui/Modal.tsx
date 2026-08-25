import * as React from "react"
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
