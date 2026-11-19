import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { 
  Sparkles, 
  ShieldCheck, 
  Clock, 
  MapPin, 
  ChevronDown, 
  Star, 
  HeartHandshake, 
  ArrowRight, 
  Check, 
  Feather,
  Flower2
} from 'lucide-react';
import { api } from '../../lib/api';

// Configuración de animación fluida basada en principios de Apple / Emil Kowalski
const smoothEase = [0.16, 1, 0.3, 1];

const fadeUp = {
  hidden: { opacity: 0, y: 24, filter: 'blur(4px)' },
  visible: { 
    opacity: 1, 
    y: 0, 
    filter: 'blur(0px)', 
    transition: { duration: 0.8, ease: smoothEase } 
  }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12, delayChildren: 0.08 }
  }
};

function Header() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 25);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.header 
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ease-out ${
        scrolled 
          ? 'bg-background/90 backdrop-blur-xl border-b border-primary-main/10 py-3 shadow-soft' 
          : 'bg-transparent py-5 md:py-6'
      }`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: smoothEase, delay: 0.1 }}
    >
      <div className="max-w-7xl mx-auto px-4 md:px-6 flex justify-between items-center">
        <a href="#" className="flex items-center gap-2 group">
          <img 
            src="/logo-full.png" 
            alt="Violett Pilates Ramos Mejía" 
            className="h-8 md:h-10 object-contain transition-transform duration-300 group-hover:scale-105" 
          />
        </a>
        
        {/* Navegación Desktop */}
        <nav className="hidden md:flex items-center gap-7 font-sans text-sm md:text-base font-medium tracking-wide text-primary-main">
          <a href="#beneficios" className="hover:text-violett-600 transition-colors">Beneficios</a>
          <a href="#experiencia" className="hover:text-violett-600 transition-colors">La Experiencia 55+5</a>
          <a href="#metodo" className="hover:text-violett-600 transition-colors">Método Débora Zárate</a>
          <a href="#membresias" className="hover:text-violett-600 transition-colors">Membresías</a>
          <a href="#faq" className="hover:text-violett-600 transition-colors">Preguntas</a>
          <Link to="/tutorial" className="hover:text-violett-600 transition-colors opacity-80 hover:opacity-100">Tutorial</Link>
          <Link 
            to="/login" 
            className="px-6 py-2.5 rounded-full bg-primary-main text-white font-medium hover:bg-violett-700 transition-all duration-300 shadow-md hover:shadow-lg transform hover:-translate-y-0.5 active:translate-y-0"
          >
            Ingresar a la App
          </Link>
        </nav>

        {/* Botón Móvil */}
        <nav className="md:hidden flex items-center gap-3">
          <Link 
            to="/login" 
            className="px-5 py-2 rounded-full bg-primary-main text-white text-sm font-medium hover:bg-violett-700 transition-all shadow-md"
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
      className={`py-16 md:py-24 px-4 md:px-6 max-w-5xl mx-auto ${className}`}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-60px" }}
      variants={staggerContainer}
    >
      {children}
    </motion.section>
  );
}

export function LandingView() {
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 800], [0, 90]);
  const opacity = useTransform(scrollY, [0, 800], [1, 0]);

  // Estado para acordeón de FAQ
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const toggleFaq = (idx: number) => {
    setOpenFaq(prev => prev === idx ? null : idx);
  };

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
        const data = res.data.results ? res.data.results : res.data; 
        return data.slice(0, 3);
      } catch (err) {
        return [];
      }
    }
  });

  const getPrecio = (clases: number) => {
    const plan = planes.find((p: any) => p.cantidad_clases === clases);
    return plan ? plan.precio : null;
  };

  const formatPrice = (val: number | null, fallback: string) => {
    if (!val) return fallback;
    return `$${val.toLocaleString('es-AR')}`;
  };

  // Preguntas frecuentes enriquecidas para Schema.org y CRO
  const faqs = [
    {
      q: "¿Cuántas alumnas hay por clase en Violett?",
      a: "Nuestras clases son estrictamente boutique: trabajamos con un máximo de 3 camillas de Reformer por turno. Esto asegura que la profesora pueda acompañar, corregir y asistir a cada alumna con el más alto nivel de dedicación y cuidado anatómico."
    },
    {
      q: "¿En qué consiste el ritual 55 + 5 de Violett?",
      a: "Cada sesión de 60 minutos se divide en dos etapas: 55 minutos de entrenamiento consciente de Pilates Reformer para activar, tonificar y flexibilizar, coronados por 5 minutos finales de masaje de descompresión miofascial asistido en cuello, hombros y columna para que te retires renovada y en calma."
    },
    {
      q: "¿Se necesita experiencia previa o flexibilidad para empezar?",
      a: "No se requiere ninguna experiencia previa. El Reformer se adapta a cada cuerpo mediante resortes de tensión progresiva. Nuestras profesoras, guiadas por el enfoque kinésico de la Lic. Débora Zárate, adaptan cada ejercicio a tus posibilidades cuidando tus articulaciones."
    },
    {
      q: "¿Qué necesito llevar para mi práctica?",
      a: "Solo ropa deportiva cómoda que te permita moverte con libertad y un par de medias antideslizantes (grip socks). Del ambiente climatizado, la suave fragancia floral, el agua y la toalla nos encargamos nosotras."
    },
    {
      q: "¿Cómo gestiono mis horarios y reservas?",
      a: "Al inscribirte tenés acceso a nuestra plataforma digital exclusiva para alumnas. Desde tu teléfono podés reservar tus turnos semanales, ver camillas disponibles o reprogramar con total autonomía y fluidez."
    },
    {
      q: "¿Dónde queda ubicado el estudio?",
      a: "Estamos ubicadas en Gral. Guido 1573, en pleno Ramos Mejía, en una zona tranquila y de fácil acceso. Un espacio diseñado para aislarte del ruido de la ciudad y conectar con tu bienestar."
    }
  ];

  return (
    <div className="min-h-screen bg-background text-primary-main font-sans selection:bg-primary-main selection:text-white overflow-x-hidden">
      <Header />

      {/* ========================================================================= */}
      {/* SECCIÓN 1: HERO DE ALTO IMPACTO Y CONVERSIÓN DIRECTA                       */}
      {/* ========================================================================= */}
      <section className="relative min-h-[92vh] md:min-h-screen flex flex-col items-center justify-center text-center px-4 md:px-6 pt-28 pb-16 overflow-hidden">
        {/* Glow de fondo atmosférico */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[320px] h-[320px] md:w-[650px] md:h-[650px] bg-violett-300/25 rounded-full blur-[90px] md:blur-[130px] -z-10 pointer-events-none" />

        <motion.div style={{ y, opacity }} className="flex flex-col items-center w-full max-w-4xl mx-auto">
          {/* Eyebrow / Pill de ubicación y categoría */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, ease: smoothEase }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violett-100/80 border border-violett-200/60 text-violett-800 text-xs md:text-sm font-semibold tracking-wider uppercase mb-6 shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-violett-600" />
            <span>Estudio Boutique en Ramos Mejía</span>
          </motion.div>

          <motion.div 
            initial="hidden" 
            animate="visible" 
            variants={staggerContainer}
            className="flex flex-col items-center"
          >
            {/* H1 Semántico con Palabras Clave Locales */}
            <motion.h1 
              variants={fadeUp} 
              className="font-laluxes text-4xl sm:text-5xl md:text-6xl lg:text-7xl mb-4 tracking-tight text-balance text-primary-main leading-[1.1]"
            >
              Violett Pilates Reformer
            </motion.h1>
            
            {/* Subtítulo Emocional Centrado */}
            <motion.p 
              variants={fadeUp} 
              className="font-marcellus text-xl sm:text-2xl md:text-3xl max-w-2xl mb-6 text-primary-main/90 leading-snug text-balance"
            >
              El arte de esculpir tu figura y habitar tu cuerpo con absoluta elegancia.
            </motion.p>
            
            {/* Propuesta de Valor Clara y Específica */}
            <motion.p 
              variants={fadeUp} 
              className="font-sans max-w-2xl text-base md:text-lg mb-8 opacity-85 leading-relaxed text-balance text-primary-main/80"
            >
              Un refugio íntimo de <strong className="font-semibold text-primary-main">máximo 3 camillas por turno</strong> donde el entrenamiento físico se une al cuidado kinésico y al bienestar integral. Disfrutá de 55 minutos de Reformer guiado paso a paso y nuestro exclusivo ritual de descompresión miofascial asistido al finalizar cada sesión.
            </motion.p>

            {/* Llamados a la Acción Primario y Secundario */}
            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto mb-12">
              <a 
                href="#membresias"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-primary-main text-white font-sans font-medium px-8 py-3.5 md:px-10 md:py-4 text-base md:text-lg rounded-full hover:bg-violett-700 hover:scale-[1.02] active:scale-95 transition-all duration-300 shadow-xl shadow-primary-main/20"
              >
                <span>✦ Ver Membresías y Disponibilidad</span>
              </a>
              <a 
                href="https://wa.me/5491157691786?text=Hola%20Deby!%20✦%20Vi%20la%20web%20de%20Violett%20Pilates%20y%20me%20gustar%C3%ADa%20consultar%20disponibilidad%20para%20empezar%20🌸"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-white/95 backdrop-blur-md text-primary-main border border-primary-main/20 font-sans font-medium px-7 py-3.5 md:px-9 md:py-4 text-base md:text-lg rounded-full hover:bg-white hover:border-primary-main transition-all duration-300 shadow-sm hover:shadow"
              >
                <span>🌸 Hablar con Débora</span>
              </a>
            </motion.div>

            {/* 3 Trust Badges de Credibilidad Visual */}
            <motion.div 
              variants={fadeUp}
              className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4 w-full max-w-3xl pt-6 border-t border-primary-main/10 text-left"
            >
              <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-white/60 backdrop-blur-sm border border-primary-main/5 shadow-xs">
                <div className="w-10 h-10 rounded-full bg-violett-100 flex items-center justify-center shrink-0 text-violett-700">
                  <Feather className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-primary-main">Máx. 3 Camillas</h4>
                  <p className="text-xs text-primary-main/70">Atención 100% personalizada</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-white/60 backdrop-blur-sm border border-primary-main/5 shadow-xs">
                <div className="w-10 h-10 rounded-full bg-violett-100 flex items-center justify-center shrink-0 text-violett-700">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-primary-main">Ritual 55' + 5'</h4>
                  <p className="text-xs text-primary-main/70">Reformer + Masaje final</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-white/60 backdrop-blur-sm border border-primary-main/5 shadow-xs">
                <div className="w-10 h-10 rounded-full bg-violett-100 flex items-center justify-center shrink-0 text-violett-700">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-primary-main">21 Años de Trayectoria</h4>
                  <p className="text-xs text-primary-main/70">Lic. Débora Zárate (Kinesióloga)</p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>
      </section>

      {/* ========================================================================= */}
      {/* SECCIÓN 2: PARA QUIÉN ES (TRANSFORMACIÓN Y BENEFICIOS TANGIBLES)          */}
      {/* ========================================================================= */}
      <div className="bg-white border-y border-primary-main/5" id="beneficios">
        <Section>
          <div className="text-center max-w-2xl mx-auto mb-12 md:mb-16">
            <motion.h2 
              variants={fadeUp} 
              className="font-marcellus text-2xl sm:text-3xl md:text-4xl mb-4 text-balance text-primary-main"
            >
              ✦ Una transformación profunda para tu cuerpo y mente
            </motion.h2>
            <motion.p 
              variants={fadeUp} 
              className="font-sans text-base md:text-lg text-primary-main/75 text-balance leading-relaxed"
            >
              Diseñado para quienes eligen regalarse un momento de autocuidado consciente, lejos del ruido y las multitudes de los gimnasios tradicionales.
            </motion.p>
          </div>

          <div className="grid md:grid-cols-2 gap-5 md:gap-6 font-sans">
            {[
              {
                icon: Sparkles,
                t: "Silueta Estilizada & Tono Profundo",
                d: "El trabajo en Reformer utiliza resortes de resistencia progresiva para activar la musculatura profunda. Alargamos y tonificamos brazos, abdomen, piernas y glúteos logrando una figura armónica y esbelta sin impacto articular."
              },
              {
                icon: ShieldCheck,
                t: "Espalda Sin Tensión & Postura Erguida",
                d: "Corregimos las compensaciones diarias. La descompresión vertebral activa alivia molestias lumbares y tensiones en hombros y cuello, devolviéndote la soltura y la elegancia natural de caminar erguida."
              },
              {
                icon: HeartHandshake,
                t: "Sin Necesidad de Experiencia Previa",
                d: "No importa tu condición física actual ni si nunca entrenaste en camilla. En Violett adaptamos cada ejercicio a tus posibilidades, guiándote con paciencia, empatía y rigurosidad biomecánica desde tu primera respiración."
              },
              {
                icon: Flower2,
                t: "El Lujo de la Intimidad y el Silencio",
                d: "Grupos estrictamente reducidos a 3 alumnas. Un espacio climatizado, envuelto en una suave fragancia floral y luz natural, donde tu profesora está pendiente de vos en cada segundo de tu práctica."
              }
            ].map((item, i) => {
              const Icon = item.icon;
              return (
                <motion.div 
                  key={i} 
                  variants={fadeUp} 
                  className="p-6 md:p-8 bg-violett-50/40 rounded-3xl border border-violett-100/80 hover:bg-violett-50 hover:border-violett-200 transition-all duration-300 shadow-xs hover:shadow-md group flex flex-col justify-between"
                >
                  <div>
                    <div className="w-12 h-12 rounded-2xl bg-white border border-violett-200/50 flex items-center justify-center text-violett-700 mb-5 shadow-xs group-hover:scale-105 transition-transform">
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="font-marcellus text-lg md:text-xl mb-2.5 text-primary-main">
                      {item.t}
                    </h3>
                    <p className="opacity-80 leading-relaxed text-sm md:text-base text-primary-main/80">
                      {item.d}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </Section>
      </div>

      {/* ========================================================================= */}
      {/* SECCIÓN 3: LA EXPERIENCIA (EL MÉTODO 55 + 5: ENTRENAMIENTO + DESCOMPRESIÓN) */}
      {/* ========================================================================= */}
      <div className="bg-primary-main/[0.02]" id="experiencia">
        <Section className="relative">
          <div className="text-center max-w-2xl mx-auto mb-12 md:mb-16">
            <motion.div 
              variants={fadeUp}
              className="inline-block px-3.5 py-1 rounded-full bg-violett-200/50 text-violett-900 text-xs font-semibold uppercase tracking-wider mb-3"
            >
              Ritual Exclusivo Violett
            </motion.div>
            <motion.h2 
              variants={fadeUp} 
              className="font-marcellus text-2xl sm:text-3xl md:text-4xl mb-4 text-balance text-primary-main"
            >
              ✦ La corona de tu día: Una hora pensada para vos
            </motion.h2>
            <motion.p 
              variants={fadeUp} 
              className="font-sans text-base md:text-lg text-primary-main/75 text-balance leading-relaxed"
            >
              Tu tiempo es tu recurso más valioso. Por eso, dividimos cada sesión en dos momentos complementarios diseñados para equilibrar fuerza y bienestar absoluto:
            </motion.p>
          </div>

          <div className="space-y-6 md:space-y-8 font-sans max-w-3xl mx-auto">
            {/* Paso 1: 55 min Reformer */}
            <motion.div 
              variants={fadeUp} 
              className="flex flex-col sm:flex-row gap-5 md:gap-7 p-6 md:p-8 bg-white rounded-3xl shadow-sm border border-primary-main/10 hover:shadow-md hover:border-violett-300 transition-all duration-300"
            >
              <div className="w-14 h-14 shrink-0 bg-primary-main text-white rounded-2xl flex items-center justify-center font-laluxes text-2xl shadow-inner shadow-black/20">
                1
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg md:text-xl font-marcellus text-primary-main">
                    55 Minutos de Pilates Reformer Consciente
                  </h3>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-violett-100 text-violett-800 font-semibold">
                    Activación
                  </span>
                </div>
                <p className="opacity-80 leading-relaxed text-sm md:text-base text-primary-main/80">
                  Sobre camillas de Reformer con resortes calibrados, realizamos secuencias fluidas que desafían el centro de energía (powerhouse). Alargamos la musculatura, fortalecemos el suelo pélvico y mejoramos la flexibilidad sin castigar las articulaciones.
                </p>
              </div>
            </motion.div>

            {/* Paso 2: 5 min Masaje */}
            <motion.div 
              variants={fadeUp} 
              className="flex flex-col sm:flex-row gap-5 md:gap-7 p-6 md:p-8 bg-white rounded-3xl shadow-sm border border-violett-300/60 bg-gradient-to-br from-white to-violett-50/30 hover:shadow-md transition-all duration-300"
            >
              <div className="w-14 h-14 shrink-0 bg-violett-700 text-white rounded-2xl flex items-center justify-center font-laluxes text-2xl shadow-inner shadow-black/20">
                2
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg md:text-xl font-marcellus text-primary-main">
                    5 Minutos de Masaje de Descompresión Asistido
                  </h3>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
                    El Toque Distintivo
                  </span>
                </div>
                <p className="opacity-80 leading-relaxed text-sm md:text-base text-primary-main/80">
                  Un regalo único que ninguna otra clase ofrece. Finalizamos tu práctica con maniobras manuales asistidas por la instructora en cuello, hombros y columna dorsal. El estrés se desvanece por completo para que salgas del estudio flotando y renovada.
                </p>
              </div>
            </motion.div>
          </div>
        </Section>
      </div>

      {/* ========================================================================= */}
      {/* SECCIÓN 4: AUTORIDAD KINÉSICA (EL MÉTODO DÉBORA ZÁRATE)                   */}
      {/* ========================================================================= */}
      <div className="bg-white border-y border-primary-main/5" id="metodo">
        <Section>
          <div className="max-w-3xl mx-auto text-center mb-10">
            <motion.div 
              variants={fadeUp}
              className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-violett-100 text-violett-800 text-xs font-semibold uppercase tracking-wider mb-4"
            >
              <ShieldCheck className="w-4 h-4 text-violett-700" />
              <span>Seguridad Biomecánica &amp; Salud</span>
            </motion.div>
            <motion.h2 
              variants={fadeUp} 
              className="font-marcellus text-2xl sm:text-3xl md:text-4xl mb-5 text-balance text-primary-main"
            >
              ✦ 21 Años de Trayectoria: El Método Débora Zárate
            </motion.h2>
            <motion.p 
              variants={fadeUp} 
              className="font-sans text-base md:text-lg text-primary-main/80 leading-relaxed mb-6 text-balance"
            >
              En Violett no improvisamos con tu cuerpo. Nuestro método fue desarrollado por la <strong className="text-primary-main">Lic. Débora Zárate</strong>, Kinesióloga y Fisiatra con más de dos décadas de trayectoria clínica y deportiva en Zona Oeste.
            </motion.p>
            <motion.p 
              variants={fadeUp} 
              className="font-sans text-sm md:text-base opacity-75 leading-relaxed text-balance"
            >
              Cada una de nuestras instructoras es seleccionada y capacitada bajo protocolos estrictos de anatomía aplicada y rehabilitación postural. Estás en manos de especialistas que cuidan tu columna, respetan tu ritmo y te acompañan con calidez en cada avance.
            </motion.p>
          </div>

          <motion.div 
            variants={fadeUp}
            className="p-6 md:p-8 rounded-3xl bg-violett-50/50 border border-violett-200/70 max-w-2xl mx-auto flex flex-col sm:flex-row items-center gap-6 text-center sm:text-left"
          >
            <div className="w-16 h-16 rounded-full bg-violett-200/80 flex items-center justify-center shrink-0 text-violett-800 font-laluxes text-2xl">
              DZ
            </div>
            <div>
              <h4 className="font-marcellus text-lg text-primary-main mb-1">
                "Cuidar tu cuerpo no es exigirte hasta el agotamiento: es moverte con inteligencia, precisión y placer."
              </h4>
              <p className="text-xs md:text-sm text-violett-700 font-medium">
                — Lic. Débora Zárate (Fundadora de Violett Pilates)
              </p>
            </div>
          </motion.div>
        </Section>
      </div>

      {/* ========================================================================= */}
      {/* SECCIÓN 5: MEMBRESÍAS DINÁMICAS + SESIÓN INAUGURAL                        */}
      {/* ========================================================================= */}
      <div id="membresias" className="bg-primary-main/[0.02]">
        <motion.section 
          className="py-16 md:py-24 px-4 md:px-6 max-w-6xl mx-auto"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-60px" }}
          variants={staggerContainer}
        >
          <div className="text-center max-w-2xl mx-auto mb-12 md:mb-14">
            <motion.h2 
              variants={fadeUp} 
              className="font-marcellus text-2xl sm:text-3xl md:text-4xl mb-4 text-balance text-primary-main"
            >
              ✦ Tu Compromiso con la Elegancia y el Cuidado
            </motion.h2>
            <motion.p 
              variants={fadeUp} 
              className="font-sans text-base md:text-lg text-primary-main/75 leading-relaxed text-balance"
            >
              Elegí la frecuencia mensual que mejor se adapte a tu rutina. Cupos estrictamente reducidos a 3 camillas por turno para garantizar exclusividad y silencio.
            </motion.p>
            <motion.p 
              variants={fadeUp} 
              className="font-sans text-xs md:text-sm italic opacity-60 mt-2"
            >
              (Aranceles actualizados en tiempo real a través de nuestra plataforma)
            </motion.p>
          </div>

          {/* Grid de 3 Planes Mensuales */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8 items-stretch mb-12">
            
            {/* PLAN 1: 4 Clases */}
            <motion.div 
              variants={fadeUp} 
              className="bg-white p-6 md:p-8 rounded-3xl border border-primary-main/10 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col h-full relative"
            >
              <h3 className="font-marcellus text-xl md:text-2xl mb-1 text-center text-primary-main">
                Pausa Delicada
              </h3>
              <div className="text-sm font-sans text-violett-700 font-medium text-center mb-5">
                4 clases al mes (1 vez por semana)
              </div>
              <p className="font-sans text-sm mb-6 flex-grow opacity-80 leading-relaxed text-center">
                Ideal para quienes desean complementar otra actividad y regalarse un encuentro semanal sagrado para descomprimir la espalda y reconectar.
              </p>
              
              <div className="p-4 rounded-2xl bg-violett-50/60 border border-violett-100 mb-6 text-center">
                <span className="text-xs uppercase tracking-wider text-primary-main/60 block mb-1">Inversión Mensual</span>
                <span className="text-2xl md:text-3xl font-bold font-sans text-primary-main">
                  {formatPrice(getPrecio(4), '$40.000')}
                </span>
              </div>

              <ul className="text-sm font-sans space-y-3 mb-8 opacity-90 text-primary-main/80">
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>1 clase semanal con reserva garantizada.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>Acceso a la plataforma de autogestión.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>Ritual de descompresión asistido incluido.</span>
                </li>
              </ul>

              <a 
                href="https://wa.me/5491157691786?text=Hola%20Deby!%20✦%20Vi%20el%20plan%20Pausa%20Delicada%20(4%20clases)%20en%20la%20web%20y%20quiero%20empezar%20🌸" 
                target="_blank"
                rel="noopener noreferrer"
                className="block text-center border-2 border-primary-main text-primary-main font-bold py-3 text-base rounded-full hover:bg-primary-main hover:text-white transition-all w-full shadow-sm hover:shadow"
              >
                Elegir 4 Clases
              </a>
              <Link to="/login" className="text-xs text-center text-primary-main/60 hover:text-primary-main hover:underline mt-2.5 block">
                ¿Ya sos alumna registrada? Ingresar ↗
              </Link>
            </motion.div>

            {/* PLAN 2: 8 Clases (DESTACADO) */}
            <motion.div 
              variants={fadeUp} 
              className="bg-primary-main text-white p-7 md:p-9 rounded-[2rem] shadow-xl md:shadow-2xl flex flex-col h-full transform lg:-translate-y-2 lg:scale-105 z-10 relative overflow-hidden border border-white/20"
            >
              <div className="absolute top-0 left-0 right-0 bg-violett-500/80 py-1.5 text-[11px] font-bold tracking-widest text-center text-white">
                ✦ PLAN RECOMENDADO Y MÁS ELEGIDO ✦
              </div>
              <h3 className="font-marcellus text-xl md:text-2xl mb-1 text-center mt-5 text-white">
                Equilibrio Radiante
              </h3>
              <div className="text-sm font-sans text-violett-200 font-medium text-center mb-5">
                8 clases al mes (2 veces por semana)
              </div>
              <p className="font-sans text-sm mb-6 flex-grow opacity-90 leading-relaxed text-center text-white/90">
                La frecuencia ideal para notar cambios visibles y duraderos. Dos encuentros semanales para moldear la silueta, fortalecer el centro y liberar dolores posturales.
              </p>

              <div className="p-4 rounded-2xl bg-white/10 border border-white/15 mb-6 text-center">
                <span className="text-xs uppercase tracking-wider text-white/70 block mb-1">Inversión Mensual</span>
                <span className="text-2xl md:text-3xl font-bold font-sans text-white">
                  {formatPrice(getPrecio(8), '$55.000')}
                </span>
              </div>

              <ul className="text-sm font-sans space-y-3 mb-8 text-white/90">
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
                  <span>2 clases semanales para máxima constancia.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
                  <span>Seguimiento kinésico personalizado continuo.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
                  <span>Flexibilidad para reprogramar turnos en la app.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
                  <span>Ritual de 5' de descompresión asistido en cada clase.</span>
                </li>
              </ul>

              <a 
                href="https://wa.me/5491157691786?text=Hola%20Deby!%20✦%20Quiero%20el%20plan%20Equilibrio%20Radiante%20(8%20clases)%20y%20coordinar%20mis%20d%C3%ADas%20🌸" 
                target="_blank"
                rel="noopener noreferrer"
                className="block text-center bg-white text-primary-main font-bold py-3.5 text-base rounded-full hover:bg-violett-50 hover:scale-[1.02] active:scale-95 transition-all w-full shadow-lg"
              >
                Quiero mi Transformación
              </a>
              <Link to="/login" className="text-xs text-center text-white/70 hover:text-white hover:underline mt-2.5 block">
                ¿Ya sos alumna registrada? Ingresar ↗
              </Link>
            </motion.div>

            {/* PLAN 3: 12 Clases */}
            <motion.div 
              variants={fadeUp} 
              className="bg-white p-6 md:p-8 rounded-3xl border border-primary-main/10 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col h-full relative"
            >
              <h3 className="font-marcellus text-xl md:text-2xl mb-1 text-center text-primary-main">
                Plenitud Total
              </h3>
              <div className="text-sm font-sans text-violett-700 font-medium text-center mb-5">
                12 clases al mes (3 veces por semana)
              </div>
              <p className="font-sans text-sm mb-6 flex-grow opacity-80 leading-relaxed text-center">
                Para quienes hacen de su bienestar su máxima prioridad. Una inmersión total para estilizar la figura con máxima agilidad, firmeza y armonía.
              </p>

              <div className="p-4 rounded-2xl bg-violett-50/60 border border-violett-100 mb-6 text-center">
                <span className="text-xs uppercase tracking-wider text-primary-main/60 block mb-1">Inversión Mensual</span>
                <span className="text-2xl md:text-3xl font-bold font-sans text-primary-main">
                  {formatPrice(getPrecio(12), '$75.000')}
                </span>
              </div>

              <ul className="text-sm font-sans space-y-3 mb-8 opacity-90 text-primary-main/80">
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>3 clases semanales con máxima prioridad de agenda.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>Ritmo acelerado de tonificación y corrección postural.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>Ritual de descompresión asistido incluido.</span>
                </li>
              </ul>

              <a 
                href="https://wa.me/5491157691786?text=Hola%20Deby!%20✦%20Quiero%20el%20plan%20Plenitud%20Total%20(12%20clases)%20y%20asegurar%20mi%20lugar%20🌸" 
                target="_blank"
                rel="noopener noreferrer"
                className="block text-center border-2 border-primary-main text-primary-main font-bold py-3 text-base rounded-full hover:bg-primary-main hover:text-white transition-all w-full shadow-sm hover:shadow"
              >
                Elegir 12 Clases
              </a>
              <Link to="/login" className="text-xs text-center text-primary-main/60 hover:text-primary-main hover:underline mt-2.5 block">
                ¿Ya sos alumna registrada? Ingresar ↗
              </Link>
            </motion.div>

          </div>

          {/* Tarjeta de Sesión Inaugural / Clase de Prueba (Reducción de Fricción) */}
          <motion.div 
            variants={fadeUp}
            className="p-6 md:p-8 rounded-3xl bg-gradient-to-r from-violett-100/70 via-white to-violett-50/70 border border-violett-200/80 shadow-sm max-w-4xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6"
          >
            <div className="text-center md:text-left">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-violett-200 text-violett-900 text-xs font-semibold uppercase tracking-wider mb-2">
                <Sparkles className="w-3.5 h-3.5" />
                <span>¿Primera vez en el estudio?</span>
              </span>
              <h3 className="font-marcellus text-xl md:text-2xl text-primary-main mb-1.5">
                Clase Inaugural de Prueba
              </h3>
              <p className="font-sans text-sm md:text-base text-primary-main/80 max-w-xl">
                ¿Querés conocer las camillas y sentir el ritual 55+5 antes de definir tu plan mensual? Agendá una clase individual con evaluación postural personalizada.
              </p>
            </div>
            <a 
              href="https://wa.me/5491157691786?text=Hola%20Deby!%20✦%20Quisiera%20coordinar%20una%20Clase%20Inaugural%20de%20prueba%20en%20Violett%20Pilates%20🌸"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 bg-primary-main text-white font-sans font-medium px-7 py-3.5 rounded-full hover:bg-violett-700 transition-all shadow-md shrink-0 text-sm md:text-base hover:scale-105 active:scale-95"
            >
              <span>🌸 Coordinar Clase Inaugural</span>
            </a>
          </motion.div>
        </motion.section>
      </div>

      {/* ========================================================================= */}
      {/* SECCIÓN 6: SOCIAL PROOF + FAQ INTERACTIVO + FOOTER                        */}
      {/* ========================================================================= */}
      
      {/* Reseñas / Testimonios */}
      <div className="bg-white border-t border-primary-main/5">
        <Section>
          <div className="text-center max-w-2xl mx-auto mb-10 md:mb-14">
            <motion.h2 
              variants={fadeUp} 
              className="font-marcellus text-2xl sm:text-3xl md:text-4xl mb-3 text-balance text-primary-main"
            >
              ✦ Ecos de nuestra comunidad
            </motion.h2>
            <motion.p 
              variants={fadeUp} 
              className="font-sans text-base md:text-lg text-primary-main/75"
            >
              Mujeres reales que transformaron su postura, su cuerpo y su energía diaria en Violett.
            </motion.p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
            {resenas.length > 0 ? (
              resenas.map((resena: any, i: number) => (
                <motion.blockquote 
                  key={i} 
                  variants={fadeUp} 
                  className="p-6 md:p-7 bg-violett-50/40 rounded-3xl border border-violett-100 flex flex-col justify-between hover:shadow-md transition-shadow relative"
                >
                  <div>
                    <div className="flex mb-3 text-amber-400">
                      {[...Array(5)].map((_, idx) => (
                        <Star 
                          key={idx} 
                          className={`w-4 h-4 ${idx < resena.estrellas ? "fill-amber-400 text-amber-400" : "text-gray-300"}`} 
                        />
                      ))}
                    </div>
                    <p className="italic text-sm md:text-base mb-5 leading-relaxed text-primary-main/80">
                      "{resena.mensaje}"
                    </p>
                  </div>
                  <footer className="font-semibold text-violett-800 text-sm border-t border-violett-200/50 pt-3">
                    — {resena.autor || 'Alumna Violett'}
                  </footer>
                </motion.blockquote>
              ))
            ) : (
              // Testimonios de alta credibilidad si la API no tiene registros
              <>
                <motion.blockquote variants={fadeUp} className="p-6 md:p-7 bg-violett-50/40 rounded-3xl border border-violett-100 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div>
                    <div className="flex mb-3 text-amber-400">
                      {[...Array(5)].map((_, idx) => (
                        <Star key={idx} className="w-4 h-4 fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                    <p className="italic text-sm md:text-base mb-5 leading-relaxed text-primary-main/80">
                      "Buscaba un lugar para empezar Pilates sin sentirme incómoda ni en un lugar ruidoso. En Violett son solo 3 camillas, la profe te corrige todo el tiempo y el masaje final de 5 minutos te deja como nueva."
                    </p>
                  </div>
                  <footer className="font-semibold text-violett-800 text-sm border-t border-violett-200/50 pt-3">
                    — Martina C. (Alumna hace 1 año)
                  </footer>
                </motion.blockquote>

                <motion.blockquote variants={fadeUp} className="p-6 md:p-7 bg-violett-50/40 rounded-3xl border border-violett-100 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div>
                    <div className="flex mb-3 text-amber-400">
                      {[...Array(5)].map((_, idx) => (
                        <Star key={idx} className="w-4 h-4 fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                    <p className="italic text-sm md:text-base mb-5 leading-relaxed text-primary-main/80">
                      "Tenía dolores lumbares fuertes por trabajar sentada 9 horas al día. El método de Débora me cambió la espalda en pocas semanas. Ya no tengo dolores y mi postura es otra."
                    </p>
                  </div>
                  <footer className="font-semibold text-violett-800 text-sm border-t border-violett-200/50 pt-3">
                    — Silvia M. (Alumna Plan 8 clases)
                  </footer>
                </motion.blockquote>

                <motion.blockquote variants={fadeUp} className="p-6 md:p-7 bg-violett-50/40 rounded-3xl border border-violett-100 flex flex-col justify-between hover:shadow-md transition-shadow">
                  <div>
                    <div className="flex mb-3 text-amber-400">
                      {[...Array(5)].map((_, idx) => (
                        <Star key={idx} className="w-4 h-4 fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                    <p className="italic text-sm md:text-base mb-5 leading-relaxed text-primary-main/80">
                      "La app para reservar es súper cómoda y el estudio siempre huele hermoso y está impecable. Es mi momento sagrado de la semana."
                    </p>
                  </div>
                  <footer className="font-semibold text-violett-800 text-sm border-t border-violett-200/50 pt-3">
                    — Carolina F. (Alumna Violett)
                  </footer>
                </motion.blockquote>
              </>
            )}
          </div>

          <motion.div variants={fadeUp} className="text-center">
            <Link 
              to="/resenas"
              className="inline-flex items-center gap-1.5 text-sm md:text-base font-semibold text-violett-800 hover:text-primary-main hover:underline transition-colors"
            >
              <span>Ver más experiencias de nuestras alumnas</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </Section>
      </div>

      {/* Preguntas Frecuentes (FAQ Accordion) */}
      <div className="bg-primary-main/[0.02]" id="faq">
        <Section className="max-w-4xl">
          <div className="text-center max-w-2xl mx-auto mb-10 md:mb-12">
            <motion.h2 
              variants={fadeUp} 
              className="font-marcellus text-2xl sm:text-3xl md:text-4xl mb-3 text-balance text-primary-main"
            >
              ✦ Preguntas Frecuentes
            </motion.h2>
            <motion.p 
              variants={fadeUp} 
              className="font-sans text-base md:text-lg text-primary-main/75"
            >
              Todo lo que necesitás saber antes de comenzar tus clases en Ramos Mejía.
            </motion.p>
          </div>

          <div className="space-y-3.5 font-sans mb-12">
            {faqs.map((faq, idx) => {
              const isOpen = openFaq === idx;
              return (
                <motion.div 
                  key={idx} 
                  variants={fadeUp} 
                  className="bg-white rounded-2xl border border-primary-main/10 overflow-hidden shadow-xs"
                >
                  <button
                    onClick={() => toggleFaq(idx)}
                    className="w-full text-left px-6 py-4.5 flex items-center justify-between gap-4 font-marcellus text-base md:text-lg text-primary-main hover:text-violett-700 transition-colors cursor-pointer"
                    aria-expanded={isOpen}
                  >
                    <span className="flex items-center gap-2">
                      <span className="text-violett-500 font-sans text-xs">✦</span>
                      <span>{faq.q}</span>
                    </span>
                    <ChevronDown 
                      className={`w-5 h-5 text-primary-main/60 shrink-0 transition-transform duration-300 ${
                        isOpen ? 'rotate-180 text-violett-700' : ''
                      }`} 
                    />
                  </button>
                  <AnimatePresence>
                    {isOpen && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3, ease: smoothEase }}
                      >
                        <div className="px-6 pb-5 pt-1 text-sm md:text-base opacity-80 leading-relaxed text-primary-main/80 border-t border-primary-main/5">
                          {faq.a}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </div>

          {/* Banner de Contacto Final */}
          <motion.div 
            variants={fadeUp}
            className="text-center p-8 md:p-10 rounded-3xl bg-primary-main text-white relative overflow-hidden shadow-xl"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-violett-400/20 rounded-full blur-[70px] pointer-events-none" />
            <h3 className="font-marcellus text-2xl md:text-3xl mb-3 text-white">
              ¿Lista para transformar tu postura y tu energía?
            </h3>
            <p className="font-sans text-sm md:text-base text-white/80 max-w-xl mx-auto mb-6">
              Los cupos son estrictamente limitados a 3 camillas por turno para cuidar la intimidad de nuestras alumnas. Contactanos para consultar horarios libres.
            </p>
            <a 
              href="https://wa.me/5491157691786?text=Hola%20Deby!%20✦%20Quisiera%20consultar%20por%20horarios%20disponibles%20en%20Violett%20Pilates%20🌸"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 bg-white text-primary-main font-sans font-bold px-8 py-3.5 rounded-full hover:bg-violett-50 transition-all shadow-md hover:scale-105 active:scale-95"
            >
              <span>✦ Hablar con Débora por WhatsApp</span>
            </a>
          </motion.div>
        </Section>
      </div>

      {/* ========================================================================= */}
      {/* FOOTER ELEGANTE + CROSS-LINK VIOLETT ESTÉTICA                             */}
      {/* ========================================================================= */}
      <footer className="py-12 md:py-16 px-6 text-center border-t border-primary-main/10 font-sans bg-background">
        <motion.div 
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto"
        >
          <img 
            src="/logo-icon.png" 
            alt="Violett Pilates" 
            className="w-12 h-12 object-contain mx-auto mb-4 opacity-80" 
          />
          <p className="font-laluxes text-xl md:text-2xl tracking-widest text-primary-main mb-1">
            Violett Pilates Reformer
          </p>
          <p className="flex items-center justify-center gap-1.5 text-sm md:text-base text-primary-main/80 mb-6">
            <MapPin className="w-4 h-4 text-violett-700" />
            <span>Gral. Guido 1573, Ramos Mejía, Prov. de Buenos Aires.</span>
          </p>

          {/* Cross-Link Estratégico a Violett Estética */}
          <div className="p-4 md:p-5 rounded-2xl bg-primary-main/[0.04] border border-primary-main/10 max-w-xl mx-auto mb-8 text-sm text-primary-main/85 leading-relaxed">
            <span className="font-semibold block sm:inline">¿Buscás tratamientos corporales, faciales y tecnología estética? </span>
            <a 
              href="https://violett.com.ar/estetica" 
              target="_blank" 
              rel="noopener noreferrer"
              className="font-bold text-violett-700 hover:text-primary-main hover:underline inline-flex items-center gap-1 transition-colors mt-1 sm:mt-0"
            >
              <span>Conocé Violett Estética en San Justo</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>

          <div className="flex flex-wrap justify-center gap-4 text-xs text-primary-main/70 pt-2 mb-4">
            <Link to="/tutorial" className="hover:underline font-bold text-primary-main">
              📚 Tutorial y Manual de la App
            </Link>
            <span>•</span>
            <Link to="/terminos" className="hover:underline">
              Términos y Condiciones
            </Link>
            <span>•</span>
            <Link to="/privacidad" className="hover:underline">
              Política de Privacidad
            </Link>
          </div>

          <p className="text-[11px] tracking-wider uppercase text-primary-main/50">
            © {new Date().getFullYear()} Violett Pilates. Todos los derechos reservados.
          </p>
        </motion.div>
      </footer>

      {/* ========================================================================= */}
      {/* BOTÓN FLOTANTE CONSERJE DE WHATSAPP                                        */}
      {/* ========================================================================= */}
      <motion.aside
        initial={{ opacity: 0, scale: 0.8, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ delay: 0.8, duration: 0.5, ease: smoothEase }}
        className="fixed bottom-5 right-5 z-50 flex items-center gap-2"
        aria-label="Atención por WhatsApp con Débora"
      >
        <a
          href="https://wa.me/5491157691786?text=Hola%20Deby!%20✦%20Estuve%20viendo%20la%20web%20de%20Violett%20Pilates%20y%20quer%C3%ADa%20hacerte%20una%20consulta%20🌸"
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center gap-3 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 text-white pl-4 pr-5 py-3 rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 active:scale-95 border border-white/20"
          title="Consultá directamente con Débora por WhatsApp"
        >
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-200 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
          </span>
          <span className="text-sm font-bold tracking-wide font-sans">
            ¿Dudas? Hablá con Débora ✦
          </span>
        </a>
      </motion.aside>
    </div>
  );
}
