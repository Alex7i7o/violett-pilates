import React from 'react';
import { Stethoscope } from 'lucide-react';

export function Doctors() {
  return (
    <section id="medicos" className="py-24 bg-primary-main relative overflow-hidden">
      <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white via-transparent to-transparent blur-2xl" />
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 relative z-10 text-center">
        <div className="w-16 h-16 rounded-2xl bg-white/10 flex items-center justify-center mx-auto mb-8 backdrop-blur-md border border-white/20">
          <Stethoscope className="w-8 h-8 text-white" />
        </div>
        
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Área de Derivación Médica</h2>
        <p className="text-xl text-primary-light/90 font-medium mb-10 max-w-2xl mx-auto">
          Una alianza estratégica pensada para potenciar y proteger el resultado de sus pacientes.
        </p>

        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 md:p-12 text-left mb-12 shadow-2xl">
          <p className="text-white/90 text-lg leading-relaxed italic mb-8">
            "Ponemos a disposición de su equipo quirúrgico un servicio de rehabilitación postoperatoria responsable y metódico. Cada paciente derivado ingresa con anamnesis rigurosa, respetando las órdenes y restricciones clínicas de su cirujano. No aplicamos aparatología agresiva en etapas inflamatorias agudas y priorizamos el drenaje manual suave para evitar dolor o desgarros de colgajos."
          </p>
          
          <h4 className="text-white font-bold mb-4">Beneficios de derivar a Violett:</h4>
          <ul className="space-y-3">
            {[
              "Reporte periódico sobre el avance de retracción cutánea y edema.",
              "Detección precoz y aviso inmediato al cirujano ante seromas o complicaciones.",
              "Coordinación de turnos prioritaria en los primeros 15 días posteriores a la cirugía."
            ].map((item, i) => (
              <li key={i} className="flex gap-3 text-white/80">
                <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-accent-gold shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <a href="https://wa.me/5491164142172" target="_blank" rel="noreferrer" className="inline-flex px-8 py-4 rounded-2xl bg-accent-gold text-white font-bold text-lg hover:bg-accent-gold-hover shadow-lg transition-all active:scale-[0.98]">
          Contactar Dirección Técnica para Derivaciones
        </a>
      </div>
    </section>
  );
}
