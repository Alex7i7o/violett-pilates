import React from 'react';
import { motion } from 'framer-motion';
import { Quote } from 'lucide-react';

export function Testimonials() {
  const testimonials = [
    {
      name: "Mariana G., 38 años",
      surgery: "Abdominoplastia + Lipoescultura",
      text: "Tenía mucho miedo a los drenajes por el dolor que todos me decían que causaba. En Violett el trato fue súper suave, no me dolió nada y a la tercera sesión ya no sentía la panza hinchada como un tambor. Mi cirujano quedó fascinado con la cicatrización."
    },
    {
      name: "Florencia M., 29 años",
      surgery: "Lipo Vaser",
      text: "Empecé a los 4 días de operarme. El seguimiento que hacen y la atención a cada detalle de la faja y las tablas me salvó de que me quedara fibrosis. Súper recomendable."
    },
    {
      name: "Comentario Médico",
      surgery: "Alianza Quirúrgica",
      text: "Derivo a mis pacientes a Violett con la absoluta tranquilidad de saber que no van a usar máquinas contraindicadas y que el drenaje manual se ejecuta con la delicadeza técnica que exige un postoperatorio."
    }
  ];

  return (
    <section id="testimonios" className="py-24 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-extrabold text-primary-main mb-4 tracking-tight">Casos de Éxito y Testimonios</h2>
          <p className="text-lg text-muted">Resultados visibles a través de la constancia y el rigor profesional.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((t, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              className="bg-background rounded-3xl p-8 border border-primary-light shadow-soft relative"
            >
              <Quote className="absolute top-8 right-8 w-8 h-8 text-accent-gold/20" />
              <p className="text-foreground font-medium italic leading-relaxed mb-8 relative z-10">"{t.text}"</p>
              <div>
                <p className="font-bold text-primary-main">{t.name}</p>
                <p className="text-sm text-muted">{t.surgery}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
