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
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.paddingRight = `${scrollbarWidth}px`;
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.paddingRight = '0px';
      document.body.style.overflow = 'unset';
    }
    return () => { 
      document.body.style.paddingRight = '0px';
      document.body.style.overflow = 'unset'; 
    }
  }, [isOpen])

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.3, ease: "easeOut" } }}
            exit={{ opacity: 0, transition: { duration: 0.35, ease: "easeInOut" } }}
            className="fixed inset-0 bg-violett-900/40 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ 
              opacity: 1, 
              scale: 1, 
              transition: { type: "spring", bounce: 0, duration: 0.6 } 
            }}
            exit={{ 
              opacity: 0, 
              scale: 0.95, 
              transition: { type: "spring", bounce: 0, duration: 0.4 } 
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
