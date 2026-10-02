import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';

// Animation configs based on Emil Kowalski / Apple Design principles
const smoothEase = [0.16, 1, 0.3, 1];

const fadeUp = {
  hidden: { opacity: 0, y: 30, filter: 'blur(4px)' },
  visible: { 
    opacity: 1, 
    y: 0, 
    filter: 'blur(0px)', 
    transition: { duration: 1, ease: smoothEase } 
  }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.1 }
  }
};

function Header() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.header 
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-out ${
        scrolled ? 'bg-background/80 backdrop-blur-xl border-b border-primary-main/10 py-3 shadow-soft' : 'bg-transparent py-5 md:py-6'
      }`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: smoothEase, delay: 0.3 }}
    >
      <div className="max-w-7xl mx-auto px-4 md:px-6 flex justify-between items-center">
        <div className="flex items-center">
          {/* Logo increased in size */}
          <img src="/logo-full.png" alt="Violett Pilates" className="h-8 md:h-10 object-contain" />
        </div>
        
        {/* Nav links increased in size */}
        <nav className="hidden md:flex items-center gap-8 font-sans text-base md:text-lg font-medium tracking-wide text-primary-main">
          <a href="#metodo" className="hover:text-violett-500 transition-colors">El Método</a>
          <a href="#experiencia" className="hover:text-violett-500 transition-colors">La Experiencia</a>
          <a href="#membresias" className="hover:text-violett-500 transition-colors">Membresías</a>
          <Link 
            to="/login" 
            className="px-6 py-2.5 rounded-full bg-primary-main text-white hover:bg-primary-hover transition-all duration-300 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
          >
            Ingresar
          </Link>
        </nav>
        {/* Mobile Nav Button */}
        <nav className="md:hidden">
          <Link 
            to="/login" 
            className="px-6 py-2.5 rounded-full bg-primary-main text-white text-base font-medium hover:bg-primary-hover transition-all shadow-md"
          >
            Ingresar
          </Link>
        </nav>
      </div>
    </motion.header>
  );
}

function Section({ children, className = "", id = "" }: { children: React.ReactNode, className?: string, id?: string }) {
  return (
    <motion.section 
      id={id}
      className={`py-20 md:py-28 px-4 md:px-6 max-w-4xl mx-auto ${className}`}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-80px" }}
      variants={staggerContainer}
    >
      {children}
    </motion.section>
  );
}

export function LandingView() {
  const { scrollY } = useScroll();
  // Hero disappears when scroll reaches 800px instead of 300px
  const y = useTransform(scrollY, [0, 800], [0, 100]);
  const opacity = useTransform(scrollY, [0, 800], [1, 0]);

  const { data: planes = [] } = useQuery({
    queryKey: ['planes_public'],
    queryFn: async () => {
      try {
        const res = await api.get('/planes/');
        return res.data.results ? res.data.results : res.data;
      } catch (err) {
        return [];
      }
    }
  });

  const { data: resenas = [] } = useQuery({
    queryKey: ['resenas_public'],
    queryFn: async () => {
      try {
        const res = await api.get('/resenas/');
        const data = res.data.results ? res.data.results : res.data; return data.slice(0, 3);
      } catch (err) {
        return [];
      }
    }
  });

  // Extract prices for 4, 8, and 12 classes
  const getPrecio = (clases: number) => {
    const plan = planes.find((p: any) => p.cantidad_clases === clases);
    return plan ? plan.precio : '---';
  };

  return (
    <div className="min-h-screen bg-background text-primary-main font-sans selection:bg-primary-main selection:text-white overflow-x-hidden">
      <Header />

      {/* Hero Section */}
      <section className="relative min-h-[90vh] md:min-h-screen flex flex-col items-center justify-center text-center px-4 md:px-6 pt-24 pb-12 overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] md:w-[600px] md:h-[600px] bg-violett-300/30 rounded-full blur-[80px] md:blur-[120px] -z-10 pointer-events-none"></div>

        <motion.div style={{ y, opacity }} className="flex flex-col items-center w-full max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.8, filter: 'blur(20px)' }}
            animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
            transition={{ duration: 1.2, ease: smoothEase }}
            className="mb-6 md:mb-8"
          >
            <img src="/logo-icon.png" alt="Violett" className="w-24 h-24 md:w-36 md:h-36 object-contain mx-auto drop-shadow-xl" />
          </motion.div>

          <motion.div 
            initial="hidden" 
            animate="visible" 
            variants={staggerContainer}
            className="flex flex-col items-center"
          >
            {/* Removed the ✦ from the main title */}
            <motion.h1 variants={fadeUp} className="font-laluxes text-4xl md:text-6xl mb-4 md:mb-6 tracking-tight text-balance text-primary-main">
              Violett Pilates
            </motion.h1>
            
            {/* Aligned right as requested when ✦ is present */}
            <motion.h2 variants={fadeUp} className="font-marcellus text-xl md:text-3xl max-w-2xl mb-6 md:mb-8 leading-relaxed md:leading-snug text-balance text-primary-main/90 text-left w-full">
              ✦ El arte de esculpir la silueta de tus sueños y habitar tu cuerpo con elegancia
            </motion.h2>
            
            <motion.p variants={fadeUp} className="font-sans text-base md:text-xl font-medium mb-6 text-violett-700">
              El estudio boutique de Pilates Reformer exclusivo en Ramos Mejía.
            </motion.p>
            <motion.p variants={fadeUp} className="font-sans max-w-2xl text-sm md:text-lg mb-10 opacity-80 leading-relaxed text-balance">
              Lejos del ruido del mundo, existe un espacio donde el tiempo parece detenerse. Un lugar impecable, envuelto en una suave fragancia floral, diseñado para la mujer que elige dedicarse tiempo a sí misma con sofisticación. En Violett, el entrenamiento físico se transforma en una expresión de belleza. Es una pausa delicada donde cada respiración y cada movimiento en el Reformer te acercan a esa figura armónica que deseás, mientras tu mente encuentra una serenidad absoluta.
            </motion.p>
            <motion.div variants={fadeUp}>
              <Link 
                to="/login"
                className="inline-flex items-center justify-center bg-primary-main text-white font-sans font-medium px-8 py-3.5 md:px-10 md:py-4 text-base md:text-lg rounded-full hover:bg-violett-700 hover:scale-[1.02] active:scale-95 transition-all duration-300 shadow-xl shadow-primary-main/20"
              >
                ✦ Descubrir mi espacio
              </Link>
            </motion.div>
          </motion.div>
        </motion.div>
      </section>

      {/* Section 2 */}
      <div className="bg-white">
        <Section>
          <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-6 md:mb-8 text-balance text-primary-main text-left w-full">
            ✦ Una vitalidad radiante para vivir al máximo
          </motion.h2>
          <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg mb-4 md:mb-6 leading-relaxed opacity-80 text-balance">
            El cuerpo es el lienzo de nuestra historia, y está diseñado para moverse con libertad, agilidad y gracia. Entendemos que el verdadero lujo es sentirte plena, ligera y sin tensiones en cada paso que das.
          </motion.p>
          <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg leading-relaxed opacity-80 text-balance">
            A través de movimientos fluidos y precisos en el Reformer, despertamos la memoria de tus músculos. No solo restauramos esa elasticidad que creías olvidada y aliviamos las molestias diarias, sino que encendemos una energía vibrante para que disfrutes tu juventud al máximo. Es el secreto de una belleza que se refleja en la firmeza de tu cuerpo y en la soltura con la que abrazás cada día.
          </motion.p>
        </Section>
      </div>

      {/* Section 3 */}
      <Section className="relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-violett-100/50 rounded-full blur-[80px] -z-10"></div>
        <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-6 md:mb-8 text-balance text-primary-main text-left w-full">
          ✦ Te esperamos exactamente como sos
        </motion.h2>
        <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg leading-relaxed opacity-80 text-balance">
          No necesitás experiencia previa ni cumplir con estándares irreales para cruzar nuestra puerta. Este es un espacio libre de juicios, un refugio creado para que seas auténticamente vos. Vení con tu historia, tus ganas y tu cuerpo tal cual es hoy; nosotras nos encargamos de guiarte, con amor, paciencia y precisión, para sacar a la luz tu versión más radiante.
        </motion.p>
      </Section>

      {/* Section 4 */}
      <div className="bg-primary-main/[0.03]">
        <Section id="experiencia" className="relative">
          <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-6 md:mb-8 text-balance text-primary-main text-left w-full">
            ✦ La corona de tu día: Una hora diseñada para vos
          </motion.h2>
          <motion.p variants={fadeUp} className="font-sans text-base md:text-lg text-center mb-10 md:mb-12 leading-relaxed opacity-80 text-balance">
            Tu tiempo es tu bien más preciado, y en Violett lo tratamos con el nivel de detalle que merecés. Cada vez que nos visitás, vivís una experiencia de 60 minutos milimétricamente pensada para tu bienestar:
          </motion.p>
          <div className="space-y-6 md:space-y-8 font-sans">
            <motion.div variants={fadeUp} className="flex flex-col md:flex-row gap-4 md:gap-6 p-6 md:p-8 bg-white rounded-3xl shadow-sm border border-primary-main/5 hover:shadow-md hover:border-violett-200 transition-all">
              <div className="w-12 h-12 md:w-14 md:h-14 shrink-0 bg-primary-main text-white rounded-full flex items-center justify-center font-laluxes text-xl md:text-2xl shadow-inner shadow-black/20">1</div>
              <div>
                <strong className="block text-lg md:text-xl font-marcellus mb-2 text-primary-main">55 Minutos de Arte y Fluidez</strong>
                <span className="opacity-80 leading-relaxed block text-sm md:text-base">Sobre el Reformer, despertamos la memoria de tus músculos. Restauramos tu elasticidad, aliviamos las tensiones diarias y moldeamos tu figura alargando la musculatura para lograr esa presencia esbelta, firme y libre de pesadez.</span>
              </div>
            </motion.div>
            <motion.div variants={fadeUp} className="flex flex-col md:flex-row gap-4 md:gap-6 p-6 md:p-8 bg-white rounded-3xl shadow-sm border border-primary-main/5 hover:shadow-md hover:border-violett-200 transition-all">
              <div className="w-12 h-12 md:w-14 md:h-14 shrink-0 bg-primary-main text-white rounded-full flex items-center justify-center font-laluxes text-xl md:text-2xl shadow-inner shadow-black/20">2</div>
              <div>
                <strong className="block text-lg md:text-xl font-marcellus mb-2 text-primary-main">5 Minutos de Pura Gloria</strong>
                <span className="opacity-80 leading-relaxed block text-sm md:text-base">Un delicado regalo final. Cerramos tu práctica con nuestro característico masaje de descompresión. Es ese instante donde el mundo desaparece, porque toda princesa merece cerrar su día sintiéndose como la realeza: renovada y en perfecta paz.</span>
              </div>
            </motion.div>
          </div>
        </Section>
      </div>

      {/* Section 5 */}
      <Section>
        <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-6 md:mb-8 text-balance text-primary-main text-left w-full">
          ✦ El Estilo de Vida Violett
        </motion.h2>
        <motion.p variants={fadeUp} className="font-sans text-base md:text-lg text-center mb-10 md:mb-12 leading-relaxed opacity-80 text-balance">
          Ser parte de nuestro estudio es abrazar una filosofía de vida. Es la delicadeza de quien sabe que cuidar su cuerpo es el acto más puro de amor propio.
        </motion.p>
        <div className="grid md:grid-cols-2 gap-4 md:gap-6 font-sans">
          {[
            { t: "La Silueta Soñada", d: "Moldeamos tu figura con la sutileza del arte, alargando la musculatura para lograr esa presencia esbelta, firme y libre de pesadez." },
            { t: "La Gracia en la Postura", d: "Corregimos desde la raíz, devolviéndote la elegancia natural de una espalda erguida y un cuello relajado. Una postura que proyecta seguridad." },
            { t: "El Privilegio de la Intimidad", d: "Grupos sumamente reducidos. Una atención que se detiene en cada detalle de tu anatomía, asegurando que cada movimiento sea impecable y cuidado." },
            { t: "La Paz Mental", d: "El estrés se disuelve entre la luz natural y nuestro característico cierre: un delicado masaje final que corona tu esfuerzo, dejándote renovada y en perfecta armonía." }
          ].map((item, i) => (
            <motion.div key={i} variants={fadeUp} className="p-6 md:p-8 bg-violett-50/50 rounded-[2rem] border border-violett-100 hover:bg-violett-50 transition-colors">
              <h3 className="font-marcellus text-lg md:text-xl mb-3 tracking-wide text-primary-main text-left w-full">✦ {item.t}</h3>
              <p className="opacity-80 leading-relaxed text-sm md:text-base">{item.d}</p>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* Section 6 */}
      <div className="bg-white">
        <Section id="metodo">
          <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-6 md:mb-8 text-balance text-primary-main text-left w-full">
            ✦ 21 Años de Excelencia: El Método Débora Zárate
          </motion.h2>
          <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg mb-4 md:mb-6 leading-relaxed opacity-80 text-balance">
            Nuestra sofisticación nace de un conocimiento profundo. El Método Violett, creado por nuestra fundadora Débora Zárate tras más de dos décadas de impecable trayectoria, garantiza un estándar de calidad insuperable.
          </motion.p>
          <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg leading-relaxed opacity-80 text-balance">
            No dejamos nada al azar. Cada instructora de nuestro equipo ha sido elegida y formada rigurosamente bajo esta misma filosofía: un equilibrio perfecto entre el conocimiento estricto de la anatomía, el cuidado y la empatía. Estás en manos de expertas que protegen tu salud integral mientras esculpen tu silueta.
          </motion.p>
        </Section>
      </div>

      {/* Section 7 */}
      <Section className="relative">
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-violett-100/50 rounded-full blur-[80px] -z-10"></div>
        <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-6 md:mb-8 text-balance text-primary-main text-left w-full">
          ✦ Todo preparado para tu llegada
        </motion.h2>
        <motion.p variants={fadeUp} className="font-sans text-base md:text-lg text-center mb-10 md:mb-12 leading-relaxed opacity-80 text-balance">
          Sabemos que dar el primer paso puede generar dudas. En Violett, hacemos que cuidarte sea la parte más fácil de tu semana.
        </motion.p>
        <div className="space-y-6 font-sans mb-12">
          {[
            { q: "¿Qué necesito llevar?", a: "Solo ropa deportiva con la que te sientas hermosa y cómoda, y tus medias antideslizantes (grip socks). Del aroma, la temperatura y la atmósfera perfecta nos encargamos nosotras." },
            { q: "¿Es para mí si nunca entrené?", a: "Absolutamente. El Reformer nos permite adaptar cada movimiento a tu cuerpo y a tu ritmo, cuidando tus articulaciones desde el primer día." },
            { q: "¿Cómo organizo mis tiempos?", a: "A través de nuestro sistema digital exclusivo, podés gestionar tu agenda y reservar tus momentos en Violett con total independencia y fluidez, sin intermediarios." }
          ].map((item, i) => (
            <motion.div key={i} variants={fadeUp} className="border-b border-primary-main/10 pb-6">
              <h3 className="font-marcellus text-lg md:text-xl mb-3 text-violett-700 text-left w-full">✦ {item.q}</h3>
              <p className="opacity-80 leading-relaxed md:pl-6 text-sm md:text-base text-left">{item.a}</p>
            </motion.div>
          ))}
        </div>
        <motion.div variants={fadeUp} className="text-center">
          <Link 
            to="/login"
            className="inline-flex items-center justify-center bg-primary-main text-white font-sans font-medium px-8 py-3.5 md:px-10 md:py-4 rounded-full hover:bg-violett-700 hover:scale-[1.02] active:scale-95 transition-all duration-300 shadow-lg shadow-primary-main/20 text-sm md:text-base"
          >
            ✦ Acceder a mi agenda personal
          </Link>
        </motion.div>
      </Section>

      {/* Section 8: Testimonials */}
      <div className="bg-primary-main/[0.03]">
        <Section>
          <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-4 md:mb-6 text-balance text-primary-main text-left w-full">
            ✦ Ecos de nuestra comunidad
          </motion.h2>
          <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg mb-10 md:mb-14 opacity-80 text-violett-800">
            Mujeres que hicieron de la elegancia y el bienestar su estilo de vida diario.
          </motion.p>
          <div className="grid md:grid-cols-2 gap-6 md:gap-8 mb-10">
            {resenas.length > 0 ? (
              resenas.map((resena: any, i: number) => (
                <motion.blockquote key={i} variants={fadeUp} className="p-6 md:p-8 bg-white rounded-3xl shadow-sm border border-primary-main/5 relative flex flex-col h-full hover:shadow-md transition-shadow">
                  <div className="absolute top-4 left-4 text-4xl text-violett-200 font-serif">"</div>
                  <div className="flex mb-4 relative z-10 justify-end">
                    {[...Array(5)].map((_, idx) => (
                      <span key={idx} className={idx < resena.estrellas ? "text-yellow-400 text-lg" : "text-gray-200 text-lg"}>★</span>
                    ))}
                  </div>
                  <p className="italic text-sm md:text-base mb-6 leading-relaxed opacity-80 relative z-10 flex-grow">
                    {resena.mensaje}
                  </p>
                  <footer className="font-bold text-violett-700 text-sm md:text-base">— {resena.autor || 'Alumna'}</footer>
                </motion.blockquote>
              ))
            ) : (
              // Fallback si todavia no hay resenas
              <>
                <motion.blockquote variants={fadeUp} className="p-6 md:p-8 bg-white rounded-3xl shadow-sm border border-primary-main/5 relative">
                  <div className="absolute top-4 left-4 text-4xl text-violett-200 font-serif">"</div>
                  <p className="italic text-sm md:text-base mb-6 leading-relaxed opacity-80 relative z-10">Buscaba un lugar que me inspirara a lograr la figura de mis sueños, y encontré un estilo de vida. Desde el aroma hasta el masaje final, todo te hace sentir radiante. Te aceptan, te cuidan y te elevan. Es la hora más linda de mi día.</p>
                  <footer className="font-bold text-violett-700 text-sm md:text-base">— Martina C.</footer>
                </motion.blockquote>
                <motion.blockquote variants={fadeUp} className="p-6 md:p-8 bg-white rounded-3xl shadow-sm border border-primary-main/5 relative">
                  <div className="absolute top-4 left-4 text-4xl text-violett-200 font-serif">"</div>
                  <p className="italic text-sm md:text-base mb-6 leading-relaxed opacity-80 relative z-10">Recuperé la firmeza y la flexibilidad, pero lo más hermoso es la energía vibrante con la que salgo para disfrutar mi día al máximo. Las profes son impecables y el método realmente cambia tu cuerpo.</p>
                  <footer className="font-bold text-violett-700 text-sm md:text-base">— Silvia M.</footer>
                </motion.blockquote>
              </>
            )}
          </div>
          <motion.div variants={fadeUp} className="text-center">
            <Link 
              to="/resenas"
              className="inline-flex items-center justify-center bg-white text-primary-main font-sans font-medium px-8 py-3.5 md:px-10 md:py-4 rounded-full border border-primary-main/10 hover:bg-primary-main hover:text-white transition-all duration-300 shadow-sm text-sm md:text-base"
            >
              Ver más reseñas
            </Link>
          </motion.div>
        </Section>
      </div>

      {/* Section 9 */}
      <Section>
        <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-6 md:mb-8 text-balance text-primary-main text-left w-full">
          ✦ Tu momento de brillar te espera
        </motion.h2>
        <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg mb-8 md:mb-10 leading-relaxed opacity-80 text-balance">
          Para mantener la excelencia, el silencio y el privilegio de la intimidad que nos caracteriza, <strong className="text-violett-700">los cupos en nuestro estudio son estrictamente limitados</strong>. Asegurá tu lugar en nuestra agenda y comenzá tu transformación.
        </motion.p>
        <div className="flex flex-col items-center">
          <ul className="space-y-4 font-sans text-left mb-10 md:mb-12 max-w-2xl bg-violett-50/50 p-6 md:p-8 rounded-[2rem] border border-violett-100 w-full">
            <motion.li variants={fadeUp} className="flex gap-3 text-sm md:text-base">
              <span className="text-violett-500 mt-0.5">✦</span>
              <span className="opacity-90"><strong className="text-primary-main">Tu Primera Invitación:</strong> Acercate a conocer la experiencia Violett y permitite sentir la belleza de un método diseñado a tu medida.</span>
            </motion.li>
            <motion.li variants={fadeUp} className="flex gap-3 text-sm md:text-base">
              <span className="text-violett-500 mt-0.5">✦</span>
              <span className="opacity-90"><strong className="text-primary-main">Membresía Glow:</strong> Garantizá tu espacio en nuestra comunidad exclusiva, manteniendo la constancia que tu cuerpo merece.</span>
            </motion.li>
          </ul>
          <motion.div variants={fadeUp}>
            <Link 
              to="/login"
              className="inline-flex items-center justify-center bg-primary-main text-white font-sans font-medium px-8 py-3.5 md:px-10 md:py-4 text-base md:text-lg rounded-full hover:bg-violett-700 hover:scale-[1.02] active:scale-95 transition-all duration-300 shadow-xl shadow-primary-main/20"
            >
              ✦ Asegurar mi lugar hoy
            </Link>
          </motion.div>
        </div>
      </Section>

      {/* Section 10: Memberships */}
      <div id="membresias" className="bg-primary-main/[0.02]">
        <motion.section 
          className="py-20 md:py-28 px-4 md:px-6 max-w-6xl mx-auto"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
          variants={staggerContainer}
        >
          <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-4 md:mb-6 text-balance text-primary-main text-left w-full">
            ✦ Tu Compromiso con la Elegancia
          </motion.h2>
          <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg mb-2 leading-relaxed opacity-80 text-balance max-w-3xl mx-auto">
            El amor propio se construye con constancia. Elegí la frecuencia que mejor se adapte a tu estilo de vida y comenzá a esculpir tu figura en nuestro refugio.
          </motion.p>
          <motion.p variants={fadeUp} className="font-sans text-center mb-10 md:mb-16 text-sm md:text-base italic opacity-60">
            (Los valores se actualizan en tiempo real)
          </motion.p>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8 items-stretch">
            {/* Plan 1 */}
            <motion.div variants={fadeUp} className="bg-white p-6 md:p-8 rounded-[2rem] border border-primary-main/10 shadow-sm hover:shadow-xl transition-shadow flex flex-col h-full relative overflow-hidden group">
              <h3 className="font-marcellus text-xl md:text-2xl mb-2 text-center text-primary-main">Pausa Delicada</h3>
              <div className="text-sm md:text-base font-sans opacity-70 text-center mb-6">(4 clases al mes)</div>
              <p className="font-sans text-sm md:text-base mb-8 flex-grow opacity-80 leading-relaxed text-center">
                Ideal para quienes buscan complementar su rutina y regalarse un momento sagrado a la semana para alinear su postura y desconectar del mundo.
              </p>
              <ul className="text-sm md:text-base font-sans space-y-3 mb-8 opacity-90">
                <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-violett-400 shrink-0"></span> 1 clase semanal garantizada.</li>
                <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-violett-400 shrink-0"></span> Acceso a plataforma de reservas.</li>
                <li className="flex items-center gap-2 font-bold text-violett-700 mt-4"><span className="w-1 h-1 rounded-full bg-violett-700 shrink-0"></span> Valor: {getPrecio(4) ? `$${getPrecio(4).toLocaleString()}` : "Cargando..."}</li>
              </ul>
              <Link to="/login" className="block text-center border-2 border-primary-main text-primary-main font-bold py-3 text-base md:text-lg rounded-full hover:bg-primary-main hover:text-white transition-colors w-full">
                Elegir este plan
              </Link>
            </motion.div>

            {/* Plan 2: Highlighted */}
            <motion.div variants={fadeUp} className="bg-primary-main text-white p-8 md:p-10 rounded-[2.5rem] shadow-xl md:shadow-2xl flex flex-col h-full transform lg:scale-105 z-10 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 bg-white/10 py-1.5 text-[10px] md:text-xs font-bold tracking-widest text-center">✦ EL MÁS ELEGIDO ✦</div>
              <h3 className="font-marcellus text-xl md:text-2xl mb-2 text-center mt-6">Equilibrio Radiante</h3>
              <div className="text-sm md:text-base font-sans opacity-80 text-center mb-6">(8 clases al mes)</div>
              <p className="font-sans text-sm md:text-base mb-8 flex-grow opacity-90 leading-relaxed text-center">
                La constancia perfecta, elegida por la mayoría de nuestras alumnas. Dos encuentros semanales para moldear tu silueta, corregir tu espalda desde la raíz y notar cambios reales.
              </p>
              <ul className="text-sm md:text-base font-sans space-y-3 mb-8">
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-white shrink-0"></span> 2 clases semanales para resultados.</li>
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-white shrink-0"></span> Acompañamiento personalizado.</li>
                <li className="flex items-center gap-2 font-bold mt-4"><span className="w-1.5 h-1.5 rounded-full bg-white shrink-0"></span> Valor: {getPrecio(8) ? `$${getPrecio(8).toLocaleString()}` : "Cargando..."}</li>
              </ul>
              <Link to="/login" className="block text-center bg-white text-primary-main font-bold py-3.5 text-base md:text-lg rounded-full hover:bg-opacity-90 hover:scale-[1.02] transition-all w-full shadow-lg">
                Quiero mi transformación
              </Link>
            </motion.div>

            {/* Plan 3 */}
            <motion.div variants={fadeUp} className="bg-white p-6 md:p-8 rounded-[2rem] border border-primary-main/10 shadow-sm hover:shadow-xl transition-shadow flex flex-col h-full relative overflow-hidden">
              <h3 className="font-marcellus text-xl md:text-2xl mb-2 text-center text-primary-main">Plenitud Total</h3>
              <div className="text-sm md:text-base font-sans opacity-70 text-center mb-6">(12 clases al mes)</div>
              <p className="font-sans text-sm md:text-base mb-8 flex-grow opacity-80 leading-relaxed text-center">
                Para quienes hacen de su bienestar su prioridad absoluta. Tres momentos a la semana de inmersión total en el Método Violett, logrando la máxima elasticidad y firmeza.
              </p>
              <ul className="text-sm md:text-base font-sans space-y-3 mb-8 opacity-90">
                <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-violett-400 shrink-0"></span> 3 clases semanales de cuidado.</li>
                <li className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-violett-400 shrink-0"></span> Máxima prioridad en nuestra agenda.</li>
                <li className="flex items-center gap-2 font-bold text-violett-700 mt-4"><span className="w-1 h-1 rounded-full bg-violett-700 shrink-0"></span> Valor: {getPrecio(12) ? `$${getPrecio(12).toLocaleString()}` : "Cargando..."}</li>
              </ul>
              <Link to="/login" className="block text-center border-2 border-primary-main text-primary-main font-bold py-3 text-base md:text-lg rounded-full hover:bg-primary-main hover:text-white transition-colors w-full">
                Elegir inmersión total
              </Link>
            </motion.div>
          </div>
        </motion.section>
      </div>

      {/* Section 11 */}
      <div className="bg-white">
        <Section>
          <motion.h2 variants={fadeUp} className="font-marcellus text-2xl md:text-4xl mb-6 md:mb-8 text-balance text-primary-main text-left w-full">
            ✦ Un entorno diseñado para tu tranquilidad
          </motion.h2>
          <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg mb-8 md:mb-10 leading-relaxed opacity-80 text-balance">
            Porque sabemos que apreciás el orden y la exclusividad, creamos una experiencia digital a la altura de nuestro estudio. A través de nuestro sistema privado, podés coordinar tus momentos en Violett con total delicadeza, gestionando tu tiempo con la misma fluidez y armonía que experimentás en nuestras camas.
          </motion.p>
          <motion.div variants={fadeUp} className="text-center">
            <Link 
              to="/login"
              className="inline-flex items-center justify-center bg-primary-main text-white font-sans font-medium px-8 py-3.5 md:px-10 md:py-4 text-base md:text-lg rounded-full hover:bg-violett-700 hover:scale-[1.02] active:scale-95 transition-all duration-300 shadow-lg shadow-primary-main/20"
            >
              ✦ Acceder a mi agenda personal
            </Link>
          </motion.div>
        </Section>
      </div>

      {/* Footer */}
      <footer className="py-12 md:py-16 px-6 text-center border-t border-primary-main/10 font-sans bg-background">
        <motion.div 
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1 }}
          className="opacity-70"
        >
          <img src="/logo-icon.png" alt="Violett" className="w-10 h-10 md:w-12 md:h-12 object-contain mx-auto mb-6 opacity-60" />
          <p className="font-laluxes mb-2 text-lg md:text-xl tracking-widest text-primary-main">Violett Pilates</p>
          <p className="mb-6 text-sm md:text-base text-primary-main/80">📍 Gral. Guido 1573, Ramos Mejía.</p>
          <p className="text-[10px] md:text-xs tracking-widest uppercase text-primary-main/60">© {new Date().getFullYear()} Violett.</p>
        </motion.div>
      </footer>
    </div>
  );
}







