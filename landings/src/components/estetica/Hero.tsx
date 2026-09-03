import React from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, Award, ShieldCheck, Stethoscope } from 'lucide-react';

export function Hero() {
  return (
    <section className="relative min-h-[90vh] flex flex-col items-center justify-center pt-14 pb-12 px-4 overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary-light/40 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent-gold/10 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="max-w-4xl mx-auto text-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <img 
            src="/isotipo.png" 
            alt="Violett Isotipo" 
            className="w-24 sm:w-32 h-auto mx-auto mb-8 drop-shadow-sm"
          />

          <span className="inline-block py-1.5 px-4 rounded-full bg-primary-light text-primary-main text-xs font-bold tracking-widest uppercase mb-6 shadow-sm border border-primary-main/10">
            Salud, Estética Avanzada y Rehabilitación
          </span>
          <h1 className="text-4xl md:text-6xl font-extrabold text-primary-main leading-tight tracking-tight mb-6">
            Especialistas en Drenaje Linfático Manual y Recuperación Postquirúrgica Integral
          </h1>
          <p className="text-lg md:text-xl text-muted font-medium mb-10 max-w-3xl mx-auto leading-relaxed">
            Más de una década acompañando la evolución de pacientes y trabajando en sinergia con cirujanos plásticos. Seguridad clínica, aparatología de vanguardia y tratamientos personalizados en San Justo.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
        >
          <a href="#contacto" className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-primary-main text-white font-bold text-lg hover:bg-primary-hover shadow-soft transition-all active:scale-[0.98] flex items-center justify-center gap-2">
            Agendá tu Evaluación Postoperatoria
          </a>
          <a href="#medicos" className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-white text-primary-main border border-primary-light font-bold text-lg hover:bg-primary-light/50 transition-all active:scale-[0.98] flex items-center justify-center gap-2 shadow-sm">
            Protocolos para Cirujanos
            <ChevronRight className="w-5 h-5" />
          </a>
        </motion.div>

        {/* Badges / Micro-social proof */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left max-w-4xl mx-auto"
        >
          <div className="flex gap-4 items-start p-4 rounded-2xl bg-white/60 backdrop-blur-sm border border-primary-light shadow-sm">
            <div className="w-10 h-10 rounded-full bg-accent-gold/20 flex items-center justify-center shrink-0">
              <Award className="w-5 h-5 text-accent-gold-hover" />
            </div>
            <div>
              <h4 className="font-bold text-foreground">+10 años de trayectoria</h4>
              <p className="text-sm text-muted leading-tight mt-1">ininterrumpida en el rubro estético y kinésico.</p>
            </div>
          </div>
          
          <div className="flex gap-4 items-start p-4 rounded-2xl bg-white/60 backdrop-blur-sm border border-primary-light shadow-sm">
            <div className="w-10 h-10 rounded-full bg-primary-light flex items-center justify-center shrink-0">
              <Stethoscope className="w-5 h-5 text-primary-main" />
            </div>
            <div>
              <h4 className="font-bold text-foreground">Avalada y recomendada</h4>
              <p className="text-sm text-muted leading-tight mt-1">por más de 5 cirujanos plásticos de zona oeste y CABA.</p>
            </div>
          </div>

          <div className="flex gap-4 items-start p-4 rounded-2xl bg-white/60 backdrop-blur-sm border border-primary-light shadow-sm">
            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h4 className="font-bold text-foreground">Atención 100% individual</h4>
              <p className="text-sm text-muted leading-tight mt-1">y seguimiento fotográfico bajo consentimiento.</p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
