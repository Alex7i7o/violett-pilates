import * as React from "react"
import { createPortal } from "react-dom"
import { motion, AnimatePresence } from "framer-motion"
import { X } from "lucide-react"
import { cn } from "../../lib/utils"

export function useMediaQuery(query: string) {
  const [matches, setMatches] = React.useState(false);

  React.useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    window.addEventListener("resize", listener);
    return () => window.removeEventListener("resize", listener);
  }, [matches, query]);

  return matches;
}

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  className?: string
}

export function Modal({ isOpen, onClose, title, children, className }: ModalProps) {
  const isMobile = useMediaQuery("(max-width: 640px)");

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

  // Apple Design: Spring physics
  const springConfig = { type: "spring", bounce: 0, duration: 0.4 };


  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <motion.div key="modal-wrapper" className="fixed inset-0 z-50 flex flex-col sm:items-center justify-end sm:justify-center pointer-events-none">
          {/* Scrim */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.3, ease: "easeOut" } }}
            exit={{ opacity: 0, transition: { duration: 0.35, ease: "easeInOut" } }}
            className="fixed inset-0 bg-primary-main/40 backdrop-blur-sm pointer-events-auto"
            onClick={onClose}
          />
          
          {/* Content */}
          <motion.div
            initial={isMobile ? { y: "100%", opacity: 1 } : { scale: 0.95, opacity: 0 }}
            animate={isMobile ? { y: 0, opacity: 1 } : { scale: 1, opacity: 1 }}
            exit={isMobile ? { y: "100%", opacity: 1 } : { scale: 0.95, opacity: 0 }}
            transition={springConfig}
            className={cn(
              "relative z-50 w-full bg-card shadow-2xl flex flex-col pointer-events-auto",
              isMobile 
                ? "mt-auto rounded-t-[32px] pb-safe max-h-[90vh]" 
                : "max-w-lg rounded-2xl sm:w-[90%] m-4",
              className
            )}
          >
            {/* Grabber handle for mobile */}
            {isMobile && (
              <div className="flex w-full items-center justify-center pt-3 pb-1" onClick={onClose}>
                <div className="h-1.5 w-12 rounded-full bg-gray-300" />
              </div>
            )}
            
            <div className={cn("flex items-center justify-between border-b border-primary-light px-6 py-4", isMobile ? "pt-2" : "")}>
              {title && <h2 className="text-xl font-semibold text-foreground">{title}</h2>}
              <button
                onClick={onClose}
                className="rounded-full p-2 text-muted transition-colors hover:bg-primary-light/50 hover:text-foreground active:scale-95 min-h-[44px] min-w-[44px] flex items-center justify-center"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto">
              {children}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  return typeof document !== 'undefined' ? createPortal(modalContent, document.body) : null;
}
