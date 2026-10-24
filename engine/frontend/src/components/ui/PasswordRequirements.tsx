import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X } from 'lucide-react';

interface Props {
  password: string;
  passwordConfirm?: string;
  isFocused?: boolean;
  showConfirm?: boolean;
}

export function PasswordRequirements({
  password,
  passwordConfirm,
  isFocused = false,
  showConfirm = false
}: Props) {
  const hasLength = password.length >= 8;
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecial = /[^A-Za-z0-9]/.test(password);
  const matches = showConfirm && password.length > 0 && password === passwordConfirm;

  // Mostramos el panel si el input tiene foco o si ya se empezó a tipear
  const shouldShow = isFocused || password.length > 0;

  if (!shouldShow) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        transition={{ duration: 0.2 }}
        className="mt-2 p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs space-y-1.5 overflow-hidden"
      >
        <p className="font-semibold text-slate-700 text-[11px] uppercase tracking-wider mb-1">
          Requisitos de la contraseña:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
          <div className={`flex items-center gap-1.5 transition-colors ${hasLength ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
            <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 text-[10px] ${hasLength ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-400'}`}>
              {hasLength ? <Check className="w-2.5 h-2.5 stroke-[3]" /> : '•'}
            </span>
            <span>Mínimo 8 caracteres</span>
          </div>

          <div className={`flex items-center gap-1.5 transition-colors ${hasUpper ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
            <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 text-[10px] ${hasUpper ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-400'}`}>
              {hasUpper ? <Check className="w-2.5 h-2.5 stroke-[3]" /> : '•'}
            </span>
            <span>Al menos una mayúscula</span>
          </div>

          <div className={`flex items-center gap-1.5 transition-colors ${hasNumber ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
            <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 text-[10px] ${hasNumber ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-400'}`}>
              {hasNumber ? <Check className="w-2.5 h-2.5 stroke-[3]" /> : '•'}
            </span>
            <span>Al menos un número</span>
          </div>

          <div className={`flex items-center gap-1.5 transition-colors ${hasSpecial ? 'text-emerald-600 font-medium' : 'text-slate-500'}`}>
            <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 text-[10px] ${hasSpecial ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-400'}`}>
              {hasSpecial ? <Check className="w-2.5 h-2.5 stroke-[3]" /> : '•'}
            </span>
            <span>Carácter especial (!@#$...)</span>
          </div>
        </div>

        {showConfirm && passwordConfirm !== undefined && passwordConfirm.length > 0 && (
          <div className={`pt-1.5 mt-1 border-t border-slate-200/60 flex items-center gap-1.5 transition-colors ${matches ? 'text-emerald-600 font-medium' : 'text-amber-600'}`}>
            <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 text-[10px] ${matches ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'}`}>
              {matches ? <Check className="w-2.5 h-2.5 stroke-[3]" /> : <X className="w-2.5 h-2.5 stroke-[3]" />}
            </span>
            <span>{matches ? 'Las contraseñas coinciden' : 'Las contraseñas no coinciden todavía'}</span>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
