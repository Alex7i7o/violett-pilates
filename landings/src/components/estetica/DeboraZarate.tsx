import React from 'react';
import { motion } from 'framer-motion';
import { GraduationCap, Users, ShieldCheck, HeartPulse } from 'lucide-react';

export function DeboraZarate() {
  const infoCards = [
    {
      icon: <GraduationCap className="w-6 h-6 text-accent-gold" />,
      title: "Kinesiología & Fisiatría",
      desc: "Más de 10 años de experiencia clínica especializada."
    },
    {
      icon: <Users className="w-6 h-6 text-accent-gold" />,
      title: "Equipo Formado",
      desc: "Personal entrenado bajo un mismo criterio técnico."
    },
    {
      icon: <ShieldCheck className="w-6 h-6 text-accent-gold" />,
      title: "Protocolo Seguro",
      desc: "Bioseguridad y prevención de fibrosis postoperatoria."
    }
  ];

  return (
    <section className="py-24 bg-background border-t border-b border-primary-light relative overflow-hidden">
      {/* Decorative background circle */}
      <div className="absolute top-0 right-0 -mr-32 -mt-32 w-96 h-96 rounded-full bg-primary-light/50 blur-3xl opacity-50" />
      
      <div className="max-w-6xl mx-auto px-4 sm:px-6 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
          >
            <div className="mb-4">
              <span className="inline-block py-1 px-3 rounded-full bg-primary-light text-primary-main text-xs font-bold tracking-wider uppercase">
                Liderazgo Clínico, Trayectoria y Formación
              </span>
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold text-primary-main mb-6 tracking-tight leading-tight">
              La profesional detrás de Violett: Débora Zárate
            </h2>
            <p className="text-lg md:text-xl text-foreground mb-6 font-medium">
              Más de una década combinando ciencia kinésica, criterio médico y calidez humana al servicio de la recuperación corporal.
            </p>
            
            <div className="space-y-6 text-muted">
              <p>
                Violett nace de la visión de <strong>Débora Zárate</strong>, Kinesióloga y Fisiatra especializada en rehabilitación postquirúrgica, drenaje linfático manual y estética médica avanzada.
              </p>
              <p>
                A lo largo de su trayectoria, Débora ha trabajado codo a codo con cirujanos plásticos y dermatólogos, comprendiendo que el postoperatorio no es un simple paso estético, sino una fase biológica determinante para la salud y el resultado final del paciente.
              </p>
            </div>
            
            <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {infoCards.map((card, idx) => (
                <div key={idx} className="bg-white p-4 rounded-2xl shadow-soft border border-primary-light/50 text-center flex flex-col items-center">
                  <div className="bg-background w-12 h-12 rounded-full flex items-center justify-center mb-3">
                    {card.icon}
                  </div>
                  <h4 className="text-sm font-bold text-primary-main mb-1">{card.title}</h4>
                  <p className="text-xs text-muted leading-relaxed">{card.desc}</p>
                </div>
              ))}
            </div>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative"
          >
            <div className="bg-white rounded-3xl p-8 md:p-10 shadow-glass border border-primary-light relative z-10">
              <div className="flex items-start gap-4 mb-6">
                <div className="bg-accent-gold/20 p-3 rounded-2xl shrink-0">
                  <HeartPulse className="w-8 h-8 text-accent-gold" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-foreground">Docencia y Formación</h3>
                  <p className="text-sm text-muted mt-1">Un puente de confianza médica</p>
                </div>
              </div>
              
              <ul className="space-y-5 mb-8">
                <li className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-accent-gold mt-2 shrink-0" />
                  <p className="text-sm text-foreground leading-relaxed">
                    <strong>Equipo propio de alto rendimiento:</strong> Formó a su propio equipo de profesionales en Violett, transmitiendo técnicas manuales exclusivas y manejo preventivo de fibrosis.
                  </p>
                </li>
                <li className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-accent-gold mt-2 shrink-0" />
                  <p className="text-sm text-foreground leading-relaxed">
                    <strong>Criterio unificado:</strong> Cada paciente recibe el mismo nivel de precisión técnica y bioseguridad, bajo la supervisión de la dirección kinésica.
                  </p>
                </li>
                <li className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-accent-gold mt-2 shrink-0" />
                  <p className="text-sm text-foreground leading-relaxed">
                    <strong>Diálogo fluido con cirujanos:</strong> Su sólida formación permite hablar el mismo lenguaje clínico y remitir partes de evolución claros.
                  </p>
                </li>
              </ul>
              
              <div className="bg-background rounded-2xl p-6 border border-primary-light relative">
                <div className="absolute -top-3 -left-2 text-4xl text-accent-gold opacity-30 font-serif">"</div>
                <p className="text-foreground text-sm md:text-base italic relative z-10 leading-relaxed font-medium">
                  Nuestra misión nunca fue hacer estética superficial, sino devolver funcionalidad, aliviar el dolor postoperatorio y acompañar a cada persona a reencontrarse con su mejor versión de forma segura.
                </p>
                <div className="mt-4 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary-light flex items-center justify-center">
                    <span className="font-bold text-primary-main">DZ</span>
                  </div>
                  <div>
                    <p className="font-bold text-primary-main text-sm">Débora Zárate</p>
                    <p className="text-xs text-muted">Kinesióloga y Fundadora</p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Background decorative elements */}
            <div className="absolute -bottom-6 -right-6 w-32 h-32 bg-accent-gold/10 rounded-full blur-2xl -z-10" />
            <div className="absolute top-1/2 -left-6 w-24 h-24 bg-primary-main/10 rounded-full blur-2xl -z-10" />
          </motion.div>

        </div>
      </div>
    </section>
  );
}
