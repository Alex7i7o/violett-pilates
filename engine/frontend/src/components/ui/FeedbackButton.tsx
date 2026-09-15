import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';
import { Button, type ButtonProps } from './Button';
import { haptics } from '../../lib/haptics';


interface FeedbackButtonProps extends ButtonProps {
  successIcon?: React.ReactNode;
  onClick?: (e: React.MouseEvent) => Promise<void> | void;
  status?: 'idle' | 'loading' | 'success';
  successText?: string;
  initialText: React.ReactNode;
}

export function FeedbackButton({ 
  onClick, 
  successText = 'Listo', 
  initialText,
  successIcon,
  className,
  variant,
  size,
  status: externalStatus,
  ...props 
}: FeedbackButtonProps) {
  const [internalStatus, setInternalStatus] = useState<'idle' | 'loading' | 'success'>('idle');
  const status = externalStatus !== undefined ? externalStatus : internalStatus;

  // Fire haptics on status change
  React.useEffect(() => {
    if (status === 'success') {
      haptics.success();
    }
  }, [status]);


  const handleClick = async (e: React.MouseEvent) => {
    if (status !== 'idle') {
      e.preventDefault();
      return;
    }
    
    if (onClick) {
      if (externalStatus === undefined) setInternalStatus('loading');
      try {
        const result = onClick(e);
        if (result instanceof Promise) {
          await result;
        }
        if (externalStatus === undefined) {
          setInternalStatus('success');
          setTimeout(() => setInternalStatus('idle'), 2000);
        }
      } catch {
        if (externalStatus === undefined) setInternalStatus('idle');
      }
    }
  };

  return (
    <motion.button
      layout
      onClick={(e) => { haptics.light(); handleClick(e); }}
      className={cn(
        "relative flex items-center justify-center whitespace-nowrap rounded-xl text-sm font-medium transition-[background-color,border-color,color] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-main disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]",
        {
          "bg-primary-main text-white hover:bg-primary-hover shadow-soft": variant === 'default' || !variant,
          "border border-primary-light bg-transparent hover:bg-primary-light/50 text-primary-main": variant === 'outline',
          "bg-rose-500 text-white hover:bg-rose-600 shadow-soft": variant === 'destructive',
          "min-h-[44px] h-[44px] sm:h-10 px-4 py-2": size === 'default' || !size,
          "min-h-[44px] h-[44px] sm:h-9 px-3": size === 'sm',
          "min-h-[44px] h-[44px] sm:h-11 px-8 text-lg": size === 'lg',
        },
        className
      )}
      
      transition={{ type: "spring", bounce: 0, duration: 0.4 }}
      style={{ overflow: 'hidden' }}
      {...(props as any)}
    >
      <AnimatePresence mode="wait" initial={false}>
        {status === 'idle' && (
          <motion.div
            key="idle"
            initial={{ opacity: 0, y: -15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 15 }}
            transition={{ type: "spring", bounce: 0, duration: 0.4 }}
            className="flex items-center justify-center gap-2"
          >
            {initialText}
          </motion.div>
        )}
        {status === 'loading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            className="flex items-center justify-center"
          >
            <svg className="animate-spin h-5 w-5 opacity-70" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </motion.div>
        )}
        {status === 'success' && (
          <motion.div
            key="success"
            initial={{ opacity: 0, y: -15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 15 }}
            transition={{ type: "spring", bounce: 0, duration: 0.4 }}
            className={cn("flex items-center justify-center gap-1.5", (variant === "default" || variant === "destructive") ? "text-white" : "text-emerald-600")}
          >
            {successIcon || (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            )}
            <span>{successText}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
}
