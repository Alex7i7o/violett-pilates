import React, { useEffect } from 'react';
import { motion, useInView } from 'framer-motion';

function FadeInView({ children, delay = 0 }: { children: React.ReactNode, delay?: number }) {
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });
  
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1], delay }}
    >
      {children}
    </motion.div>
  );
}

export default function PilatesLanding() {
  React.useEffect(() => {
    document.title = "Violett Pilates";
    
    // Función para actualizar el favicon según el tema
    const updateFavicon = (isDark: boolean) => {
      let link = document.querySelector("link[rel~='icon']") as HTMLLinkElement;
      if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
      }
      link.href = isDark ? '/favicon-pilates-dark.png' : '/favicon-pilates.png';
    };

    // Detectar tema inicial
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    updateFavicon(mediaQuery.matches);

    // Escuchar cambios de tema
    const handleChange = (e: MediaQueryListEvent) => updateFavicon(e.matches);
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return (
    <div className="min-h-screen overflow-x-hidden bg-background text-foreground font-sans selection:bg-primary-main selection:text-white">
      {/* HEADER */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-primary-main/10">
        <div className="max-w-5xl mx-auto px-6 h-20 flex items-center justify-between">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1] }}
            className="font-bold text-xl tracking-wide flex items-center gap-2"
          >
            <img src="/logo-wordmark.png" alt="Violett Pilates" className="h-16 object-contain" />
          </motion.div>
          
          <motion.a 
            href="/pilates/app/"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1] }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-6 py-2.5 bg-primary-main text-white rounded-full text-sm font-medium shadow-sm transition-colors hover:bg-primary-hover"
          >
            Ingresar
          </motion.a>
        </div>
      </header>

      <main className="pt-32 pb-24">
        {/* HERO SECTION */}
        <section className="relative max-w-4xl mx-auto px-6 pt-12 pb-24 text-center">
          <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-primary-light/60 rounded-full blur-[120px] pointer-events-none -z-20" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent-gold/10 rounded-full blur-[100px] pointer-events-none -z-20" />
          <img src="/logo-icon.png" alt="Violett" className="h-20 mx-auto mb-6 object-contain drop-shadow-sm opacity-90" />
            <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
            className="text-5xl md:text-7xl font-bold tracking-tight text-primary-main mb-6"
          >
            El Arte de Tu<br />Bienestar
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.23, 1, 0.32, 1] }}
            className="text-lg md:text-xl text-gray-600 leading-relaxed max-w-2xl mx-auto"
          >
            Hay un momento en el día que te pertenece solo a vos. En nuestro estudio exclusivo en Ramos Mejía, transformamos el entrenamiento en un refugio personal. No buscamos el agotamiento extremo; buscamos el equilibrio. Diseñamos un espacio donde el movimiento se convierte en tu momento de reconexión, permitiéndote pausar el ruido exterior para cultivar tu versión más elegante, serena y empoderada.
          </motion.p>
        </section>

        {/* TRANSFORMATION SECTION */}
        <section className="max-w-4xl mx-auto px-6 py-24 border-t border-primary-main/10">
          <FadeInView>
            <div className="mb-4 text-primary-main opacity-50">✦ Tu Transformación</div>
            <h2 className="text-3xl md:text-4xl font-bold mb-6 text-primary-main">Abrazar una salud consciente y estética.</h2>
            <p className="text-lg text-gray-600 mb-12 leading-relaxed">
              Redefinimos tu rutina para que cada clase se sienta como un regalo hacia tu propio cuerpo, logrando resultados que trascienden el estudio y te acompañan en tu crecimiento personal y profesional:
            </p>
          </FadeInView>

          <div className="grid md:grid-cols-2 gap-8">
            {[
              { title: "Silueta Estilizada", desc: "Ejercicios guiados que esculpen y definen tu figura con gracia, alargando la musculatura sin generar tensión innecesaria." },
              { title: "Ligereza y Libertad", desc: "Ganá flexibilidad y aliviá tensiones acumuladas para caminar por la vida con una postura erguida, ágil y libre de dolores." },
              { title: "Renovación Mental", desc: "Una atmósfera acústica y visualmente cuidada que disuelve el estrés y recarga tu energía diaria." },
              { title: "Pertenencia", desc: "Grupos íntimos y atención dedicada, porque tu bienestar integral merece el nivel más alto de cuidado y detalle." }
            ].map((item, i) => (
              <FadeInView key={i} delay={i * 0.1}>
                <div className="bg-white/80 backdrop-blur-md p-8 rounded-3xl shadow-soft border border-primary-light hover:-translate-y-1 transition-all duration-300 relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-br from-primary-light/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10" />
                  <h3 className="text-xl font-bold mb-3 text-primary-main">{item.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{item.desc}</p>
                </div>
              </FadeInView>
            ))}
          </div>
        </section>

        {/* COMMUNITY SECTION */}
        <section className="bg-primary-main text-white py-24">
          <div className="max-w-4xl mx-auto px-6">
            <FadeInView>
              <div className="mb-4 text-white/50">✦ Inspiración y Comunidad</div>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">Rodéate de mujeres que, como vos, eligen priorizarse todos los días.</h2>
              <p className="text-lg text-white/80 mb-16 leading-relaxed max-w-2xl">
                Nuestra embajadora digital, Violetita ✦, te acompaña desde las redes recordando que tu constancia genera cambios reales. Lo que se vive en nuestros Reformers se refleja en las palabras de nuestra comunidad:
              </p>
            </FadeInView>

            <div className="grid md:grid-cols-2 gap-8">
              {[
                { quote: "Encontré mi santuario. Salgo de cada clase sintiéndome más alta, más liviana y con una paz mental increíble.", author: "Lucía M." },
                { quote: "Nunca pensé que entrenar me daría tanta seguridad. Mi postura cambió por completo; es mi inversión favorita en mí misma.", author: "Valentina G." }
              ].map((item, i) => (
                <FadeInView key={i} delay={i * 0.1}>
                  <div className="bg-white/10 p-8 rounded-3xl backdrop-blur-sm border border-white/10">
                    <p className="text-lg italic mb-6 leading-relaxed">"{item.quote}"</p>
                    <p className="font-medium text-white/70">— {item.author}</p>
                  </div>
                </FadeInView>
              ))}
            </div>
          </div>
        </section>

        {/* FINAL CTA SECTION */}
        <section className="max-w-3xl mx-auto px-6 py-32 text-center">
          <FadeInView>
            <div className="mb-4 text-primary-main opacity-50">✦ Tu Espacio Te Espera</div>
            <h2 className="text-4xl md:text-5xl font-bold mb-8 text-primary-main">Diseñamos una experiencia sin fricciones desde el primer contacto.</h2>
            <p className="text-lg text-gray-600 mb-12 leading-relaxed">
              Nuestro sistema de reservas te permite organizar tu agenda con la misma fluidez con la que fluís en cada clase. Da el primer paso hacia el estilo de vida que te inspira.
            </p>
            
            <div className="flex flex-col items-start text-left max-w-lg mx-auto mb-16 space-y-4 text-gray-700">
              <p><strong className="text-primary-main">Tu Sesión Inaugural:</strong> Vení a conocer tu nuevo lugar favorito.</p>
              <p><strong className="text-primary-main">Membresía Glow:</strong> Asegurá tu lugar fijo en nuestros grupos reducidos.</p>
              <p><strong className="text-primary-main">Bienestar 360:</strong> Complementá tu equilibrio integrando los cuidados de Violett Estética.</p>
            </div>

            <motion.a 
              href="/pilates/app/"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="inline-flex items-center justify-center gap-2 px-10 py-5 bg-primary-main text-white rounded-2xl text-lg font-bold shadow-soft transition-all hover:bg-primary-hover active:scale-[0.98]"
            >
              ✦ Reservar Mi Momento
            </motion.a>
          </FadeInView>
        </section>
      </main>
      
      {/* FOOTER */}
      <footer className="bg-gray-50 py-12 border-t border-gray-200 text-center text-gray-500 text-sm">
        <p>© 2026 Violett Pilates. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}