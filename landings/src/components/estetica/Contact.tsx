import React, { useState } from 'react';
import { MapPin, Clock, Navigation } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function Contact() {
  const [formData, setFormData] = useState({
    nombre: '',
    telefono: '',
    tipo: '',
    mensaje: ''
  });
  
  const [errors, setErrors] = useState<Record<string, boolean>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Custom validation
    const newErrors: Record<string, boolean> = {};
    if (!formData.nombre.trim()) newErrors.nombre = true;
    if (!formData.telefono.trim()) newErrors.telefono = true;
    if (!formData.tipo) newErrors.tipo = true;
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setErrors({});
    
    // Generate WhatsApp Message
    const tiposMap: Record<string, string> = {
      post: 'Recuperación Postquirúrgica',
      corp: 'Estética Corporal / Maderoterapia',
      fac: 'Tratamientos Faciales',
      med: 'Consulta Profesional / Derivación Médica'
    };
    
    const texto = `Hola Violett! Mi nombre es *${formData.nombre.trim()}*.\n\nQuisiera consultar por: *${tiposMap[formData.tipo]}*.\n\nMi teléfono es: ${formData.telefono.trim()}${formData.mensaje.trim() ? `\n\nComentario adicional: ${formData.mensaje.trim()}` : ''}`;
    
    const url = `https://wa.me/5491164142172?text=${encodeURIComponent(texto)}`;
    window.open(url, '_blank');
  };

  const inputClass = (hasError: boolean) => 
    `w-full px-4 py-3 rounded-xl border bg-white focus:outline-none focus:ring-2 transition-colors ${
      hasError 
        ? 'border-red-500 focus:ring-red-500/50' 
        : 'border-primary-light focus:ring-primary-main/50'
    }`;

  return (
    <section id="contacto" className="py-24 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
          
          <div>
            <h2 className="text-3xl font-extrabold text-primary-main mb-6 tracking-tight">Ubicación e Instalaciones</h2>
            <p className="text-lg text-muted mb-8">Ubicados estratégicamente en el corazón de San Justo, a pocas cuadras de los principales accesos y centros médicos de la zona oeste.</p>
            
            <div className="space-y-6 mb-8">
              <div className="flex gap-4 items-start">
                <MapPin className="w-6 h-6 text-accent-gold shrink-0 mt-1" />
                <div>
                  <h4 className="font-bold text-foreground">Dirección</h4>
                  <p className="text-muted">Comisionado Indart 2822<br/>San Justo, Provincia de Buenos Aires.</p>
                </div>
              </div>
              <div className="flex gap-4 items-start">
                <Navigation className="w-6 h-6 text-accent-gold shrink-0 mt-1" />
                <div>
                  <h4 className="font-bold text-foreground">Zona de Influencia</h4>
                  <p className="text-muted">Ramos Mejía, San Justo, Haedo, Morón y alrededores.</p>
                </div>
              </div>
              <div className="flex gap-4 items-start">
                <Clock className="w-6 h-6 text-accent-gold shrink-0 mt-1" />
                <div>
                  <h4 className="font-bold text-foreground">Horarios de Atención</h4>
                  <p className="text-muted">Lunes a Sábados con turno coordinado previamente.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-background rounded-3xl p-8 border border-primary-light shadow-glass">
            <h3 className="text-2xl font-bold text-primary-main mb-6">Agendá tu Evaluación Inicial</h3>
            <form className="space-y-5" onSubmit={handleSubmit} noValidate>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">Nombre y Apellido</label>
                <input 
                  type="text" 
                  className={inputClass(errors.nombre)}
                  placeholder="Tu nombre" 
                  value={formData.nombre}
                  onChange={(e) => setFormData({...formData, nombre: e.target.value})}
                />
                <AnimatePresence>
                  {errors.nombre && (
                    <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="text-red-500 text-sm mt-1 font-medium">Este campo es obligatorio</motion.p>
                  )}
                </AnimatePresence>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">Teléfono / WhatsApp</label>
                <input 
                  type="tel" 
                  className={inputClass(errors.telefono)}
                  placeholder="+54 9 11..." 
                  value={formData.telefono}
                  onChange={(e) => setFormData({...formData, telefono: e.target.value})}
                />
                <AnimatePresence>
                  {errors.telefono && (
                    <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="text-red-500 text-sm mt-1 font-medium">Este campo es obligatorio</motion.p>
                  )}
                </AnimatePresence>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">Tipo de Consulta</label>
                <select 
                  className={inputClass(errors.tipo)}
                  value={formData.tipo}
                  onChange={(e) => setFormData({...formData, tipo: e.target.value})}
                >
                  <option value="">Seleccioná una opción...</option>
                  <option value="post">Recuperación Postquirúrgica</option>
                  <option value="corp">Estética Corporal / Maderoterapia</option>
                  <option value="fac">Tratamientos Faciales</option>
                  <option value="med">Consulta Profesional / Derivación Médica</option>
                </select>
                <AnimatePresence>
                  {errors.tipo && (
                    <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="text-red-500 text-sm mt-1 font-medium">Seleccioná una opción</motion.p>
                  )}
                </AnimatePresence>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-foreground mb-2">Mensaje Adicional</label>
                <textarea 
                  rows={3} 
                  className="w-full px-4 py-3 rounded-xl border border-primary-light bg-white focus:outline-none focus:ring-2 focus:ring-primary-main/50 resize-none" 
                  placeholder="Contanos brevemente sobre tu caso..."
                  value={formData.mensaje}
                  onChange={(e) => setFormData({...formData, mensaje: e.target.value})}
                ></textarea>
              </div>
              
              <button type="submit" className="w-full py-4 rounded-xl bg-primary-main text-white font-bold text-lg hover:bg-primary-hover transition-colors shadow-soft">
                Solicitar Turno por WhatsApp
              </button>
            </form>
          </div>

        </div>
      </div>
    </section>
  );
}
