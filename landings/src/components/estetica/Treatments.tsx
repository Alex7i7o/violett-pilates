import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

export function Treatments() {
  return (
    <section id="tratamientos" className="py-24 bg-primary-light/30">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="mb-20">
          <span className="text-primary-main font-bold tracking-wider uppercase text-sm mb-2 block">
            Especialidad Postquirúrgica & Kinesiología
          </span>
          <h2 className="text-3xl md:text-5xl font-extrabold text-foreground mb-8 tracking-tight">
            Protocolo de Recuperación Postoperatoria
          </h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <p className="text-lg text-muted">
                <strong>Indicado para:</strong> Lipoescultura, Lipo vaser / HD, Abdominoplastia, Dermolipectomía, Mastoplastia (aumento/reducción), Rinoplastia y Lifting facial.
              </p>
              
              <ul className="space-y-4">
                {[
                  "Drenaje Linfático Manual (técnicas Vodder / Leduc adaptadas).",
                  "Manejo preventivo y terapéutico de fibrosis tisular.",
                  "Descongestión de hematomas y control de puntos de tensión.",
                  "Asesoramiento y ajuste postural de fajas, tablas y apósitos."
                ].map((item, i) => (
                  <li key={i} className="flex gap-3">
                    <div className="mt-1 w-6 h-6 rounded-full bg-accent-gold/20 flex items-center justify-center shrink-0">
                      <Check className="w-4 h-4 text-accent-gold-hover" />
                    </div>
                    <span className="text-muted font-medium">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="bg-white rounded-3xl p-8 border border-primary-light shadow-glass">
              <h3 className="text-2xl font-bold text-primary-main mb-6">Planes y Paquetes</h3>
              <div className="space-y-6">
                <div className="flex justify-between items-center pb-6 border-b border-gray-100">
                  <div>
                    <h4 className="font-bold text-foreground text-lg">Evaluación / Diagnóstico Inicial</h4>
                    <p className="text-sm text-muted mt-1">Primer contacto post-cirugía</p>
                  </div>
                  <span className="text-xl font-extrabold text-primary-main">$65.000</span>
                </div>
                <div className="flex justify-between items-center pb-6 border-b border-gray-100">
                  <div>
                    <h4 className="font-bold text-foreground text-lg">Módulo Intensivo</h4>
                    <p className="text-sm text-muted mt-1">Paquete de 5 sesiones</p>
                  </div>
                  <span className="text-xl font-extrabold text-primary-main">$300.000</span>
                </div>
                <div className="flex justify-between items-center bg-primary-light/50 -mx-4 p-4 rounded-2xl border border-primary-main/10">
                  <div>
                    <h4 className="font-bold text-primary-main text-lg">Protocolo Integral</h4>
                    <p className="text-sm text-primary-main/70 mt-1">10 sesiones de recuperación continua</p>
                    <span className="inline-block mt-2 text-xs font-bold bg-accent-gold text-white px-2 py-1 rounded-lg uppercase tracking-wide">
                      Ahorrás $100.000
                    </span>
                  </div>
                  <span className="text-2xl font-extrabold text-primary-main">$550.000</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Other Treatments Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-white rounded-3xl p-8 border border-primary-light shadow-soft"
          >
            <span className="text-accent-gold-hover font-bold tracking-wider uppercase text-xs mb-2 block">
              Estética Corporal Avanzada
            </span>
            <h3 className="text-2xl font-bold text-primary-main mb-6">Modelación, Firmeza y Reducción</h3>
            <ul className="space-y-5">
              <li>
                <strong className="block text-foreground mb-1">Maderoterapia Corporal</strong>
                <span className="text-sm text-muted">Remodelado de contornos, activación circulatoria y estimulación fascial profunda.</span>
              </li>
              <li>
                <strong className="block text-foreground mb-1">Masajes Reductores y Anticelulíticos</strong>
                <span className="text-sm text-muted">Trabajo localizado en tejido adiposo y mejora del retorno venoso.</span>
              </li>
              <li>
                <strong className="block text-foreground mb-1">Aparatología de Alta Gama</strong>
                <span className="text-sm text-muted">Radiofrecuencia y electroporación para reafirmación dérmica y elasticidad de la piel.</span>
              </li>
            </ul>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-3xl p-8 border border-primary-light shadow-soft"
          >
            <span className="text-accent-gold-hover font-bold tracking-wider uppercase text-xs mb-2 block">
              Estética Facial & Bienestar
            </span>
            <h3 className="text-2xl font-bold text-primary-main mb-6">Revitalización y Salud de la Piel</h3>
            <ul className="space-y-5">
              <li>
                <strong className="block text-foreground mb-1">Higiene y Desintoxicación</strong>
                <span className="text-sm text-muted">Limpieza facial profunda con extracción higiénica.</span>
              </li>
              <li>
                <strong className="block text-foreground mb-1">Renovación Celular</strong>
                <span className="text-sm text-muted">Peeling acorde al fototipo cutáneo.</span>
              </li>
              <li>
                <strong className="block text-foreground mb-1">Drenaje Facial Descongestivo</strong>
                <span className="text-sm text-muted">Post-cirugía facial o de párpados.</span>
              </li>
              <li>
                <strong className="block text-foreground mb-1">Terapias de Relajación</strong>
                <span className="text-sm text-muted">Masajes descontracturantes y técnicas integrales antiestrés.</span>
              </li>
            </ul>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
