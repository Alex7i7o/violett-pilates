import React from 'react';
import { motion } from 'framer-motion';
import { PhoneCall, HeartHandshake, ShieldAlert } from 'lucide-react';

export function Credibility() {
  return (
    <section id="credibilidad" className="py-24 bg-white relative">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16 max-w-3xl mx-auto">
          <span className="text-accent-gold-hover font-bold tracking-wider uppercase text-sm mb-2 block">
            Criterio Clínico y Confianza Profesional
          </span>
          <h2 className="text-3xl md:text-5xl font-extrabold text-primary-main mb-6 tracking-tight">
            Por qué los profesionales de la salud confían en Violett
          </h2>
          <p className="text-lg text-muted">
            La recuperación postquirúrgica no admite improvisaciones. Entendemos que el éxito de una intervención quirúrgica depende en un 50% de la técnica del cirujano y en un 50% del cuidado postoperatorio inmediato. Trabajamos bajo estrictos protocolos kinésicos y estéticos que respetan los tiempos biológicos de cicatrización y desinflamación.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            {
              icon: PhoneCall,
              title: "Comunicación Directa con Quirófano",
              desc: "Mantenemos un canal abierto con el médico tratante, remitiendo informes de evolución tisular, drenaje y respuesta a la compresión de fajas."
            },
            {
              icon: HeartHandshake,
              title: "Fisiatría y Drenaje Especializado",
              desc: "Aplicamos técnicas manuales indoloras diseñadas para reducir seromas, prevenir fibrosis subcutánea y optimizar la reabsorción edematosa sin comprometer las suturas."
            },
            {
              icon: ShieldAlert,
              title: "Bioseguridad y Consentimiento",
              desc: "Ficha de evaluación integral de ingreso, registro de dolor, zonas críticas y seguimiento riguroso bajo consentimiento de uso de datos e imagen."
            }
          ].map((item, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.5, delay: idx * 0.1 }}
              className="bg-background rounded-3xl p-8 border border-primary-light shadow-soft hover:shadow-glass transition-shadow"
            >
              <div className="w-14 h-14 rounded-2xl bg-primary-light flex items-center justify-center mb-6">
                <item.icon className="w-7 h-7 text-primary-main" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">{item.title}</h3>
              <p className="text-muted leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
