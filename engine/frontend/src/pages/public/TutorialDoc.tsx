import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Search, 
  Smartphone, 
  Calendar, 
  Clock, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle, 
  MessageSquare, 
  Sparkles, 
  CreditCard, 
  Repeat, 
  User, 
  Bell, 
  HelpCircle, 
  ChevronDown, 
  ChevronRight, 
  Share, 
  Download, 
  ExternalLink,
  HeartHandshake,
  Check,
  Zap,
  Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface FAQItem {
  pregunta: string;
  respuesta: string;
  categoria: string;
}

export function TutorialDoc() {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'todos' | 'instalacion' | 'reservas' | 'cancelaciones' | 'fijos' | 'planes' | 'whatsapp' | 'faq'>('todos');
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  const toggleFaq = (idx: number) => {
    setExpandedFaq(prev => prev === idx ? null : idx);
  };

  const faqs: FAQItem[] = [
    {
      categoria: 'reservas',
      pregunta: '¿Con cuánta anticipación puedo reservar una clase?',
      respuesta: 'Podés reservar tus turnos en cualquier momento del mes mientras tengas clases disponibles en tu abono. Te recomendamos agendarte con anticipación para asegurar tu camilla en tus horarios preferidos (recuerda que cada turno tiene un máximo exclusivo de 3 camillas).'
    },
    {
      categoria: 'cancelaciones',
      pregunta: '¿Cómo funciona la regla de cancelación de 24 horas?',
      respuesta: 'En Violett Pilates cuidamos tu tiempo y el de nuestros profesores. Si cancelás con 24 horas o más de anticipación respecto al inicio de la clase, el sistema te reintegra el crédito automáticamente para que lo utilices en otro turno del mes. Si cancelás con menos de 24 hs, la clase se computa como tomada y no es posible recuperar el crédito.'
    },
    {
      categoria: 'fijos',
      pregunta: '¿Puedo tener un horario fijo todas las semanas?',
      respuesta: '¡Sí! Si tu rutina es constante (por ejemplo, todos los martes y jueves a las 19:00 hs), podés solicitarle a Débora en la recepción que te asigne un "Horario Fijo". El sistema te reservará automáticamente tus camillas todas las semanas sin que tengas que hacerlo a mano.'
    },
    {
      categoria: 'planes',
      pregunta: '¿Qué vigencia tienen los planes mensuales?',
      respuesta: 'Todos los planes mensuales (4, 8 y 12 clases) tienen una vigencia estricta de 30 días corridos a partir de la fecha de inicio. Los créditos no consumidos dentro del ciclo de 30 días no se acumulan para el mes siguiente.'
    },
    {
      categoria: 'planes',
      pregunta: '¿Cómo renuevo mi abono o pago una clase suelta?',
      respuesta: 'Podés abonar por transferencia bancaria solicitando el Alias a través de la app o por nuestro WhatsApp oficial, o bien en efectivo o transferencia directamente en la recepción del estudio con Débora. Una vez acreditado el pago, tus clases se habilitan al instante.'
    },
    {
      categoria: 'whatsapp',
      pregunta: '¿Qué puedo pedirle al asistente de WhatsApp de Violett?',
      respuesta: 'El asistente oficial de Violett en WhatsApp funciona las 24 horas. Podés consultar tus clases agendadas ("¿Cuándo tengo clases?"), ver horarios libres de la semana ("¿Hay lugar mañana a la tarde?"), reservar o cancelar turnos ("Reservame el jueves 19hs"), consultar tu saldo de créditos y enviar fotos de comprobantes de pago.'
    },
    {
      categoria: 'general',
      pregunta: '¿Qué debo llevar para mi primera clase de Reformer?',
      respuesta: 'Recomendamos asistir con ropa cómoda deportiva (calzas o pantalón elastizado y remera). Es obligatorio el uso de medias (preferentemente antideslizantes) para trabajar sobre el Reformer con total higiene y seguridad. En el estudio disponemos de dispensers de agua y un ambiente aromatizado diseñado para tu relajación.'
    },
    {
      categoria: 'general',
      pregunta: 'Tengo dolor lumbar o una lesión, ¿puedo hacer igual?',
      respuesta: '¡Por supuesto! Pilates Reformer es uno de los métodos más recomendados para rehabilitación y fortalecimiento postural. Te pedimos que completes tus antecedentes en la sección "Mi Perfil" de la app para que la instructora adapte cada ejercicio a tu condición.'
    }
  ];

  const filteredFaqs = useMemo(() => {
    return faqs.filter(f => {
      const matchesSearch = searchTerm === '' || 
        f.pregunta.toLowerCase().includes(searchTerm.toLowerCase()) || 
        f.respuesta.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCat = activeTab === 'todos' || activeTab === 'faq' || f.categoria === activeTab;
      return matchesSearch && matchesCat;
    });
  }, [searchTerm, activeTab]);

  return (
    <div className="min-h-screen bg-[#FAFAFC] text-[#2B1A53] selection:bg-purple-100 selection:text-purple-900 pb-20">
      
      {/* TOPBAR / HEADER BOUTIQUE */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-purple-100/70 shadow-xs">
        <div className="max-w-6xl mx-auto px-4 h-16 sm:h-20 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link 
              to="/" 
              className="p-2 sm:px-3 sm:py-2 rounded-xl border border-purple-200/60 bg-purple-50/50 hover:bg-purple-100/60 text-purple-900 text-xs sm:text-sm font-semibold flex items-center gap-1.5 transition-all shadow-2xs"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Volver a la App</span>
            </Link>
            <div className="h-6 w-px bg-purple-200/50 hidden sm:block" />
            <div className="flex items-center gap-2">
              <span className="font-serif text-lg sm:text-2xl font-bold tracking-tight text-[#34236F]">
                Violett Pilates ✦
              </span>
              <span className="text-[10px] sm:text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 border border-purple-200 uppercase tracking-widest hidden md:inline">
                Manual de Alumnas
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href="https://wa.me/5491157691786"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3.5 py-1.5 sm:py-2 rounded-xl bg-[#25D366]/10 text-emerald-800 border border-emerald-300/60 hover:bg-[#25D366]/20 font-semibold text-xs sm:text-sm flex items-center gap-2 transition-all"
            >
              <MessageSquare className="w-4 h-4 text-[#25D366]" />
              <span className="hidden sm:inline">WhatsApp Oficial</span>
            </a>
            <Link 
              to="/" 
              className="px-4 py-1.5 sm:py-2 rounded-xl bg-[#34236F] hover:bg-[#2A1C5A] text-white font-bold text-xs sm:text-sm shadow-sm transition-all"
            >
              Ingresar
            </Link>
          </div>
        </div>
      </header>

      {/* HERO BANNER EDITORIAL */}
      <section className="relative overflow-hidden bg-gradient-to-b from-purple-50/80 via-white to-[#FAFAFC] pt-10 sm:pt-16 pb-12 sm:pb-20 border-b border-purple-100/50">
        <div className="max-w-4xl mx-auto px-4 text-center space-y-4 sm:space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-100/80 border border-purple-200/80 text-purple-900 text-xs font-semibold shadow-2xs">
            <Sparkles className="w-3.5 h-3.5 text-purple-700" />
            Guía de Uso Paso a Paso
          </div>

          <h1 className="font-serif text-3xl sm:text-5xl lg:text-6xl font-bold text-[#34236F] tracking-tight leading-tight">
            Aprendé a disfrutar de tu experiencia en Violett
          </h1>

          <p className="text-muted text-sm sm:text-lg max-w-2xl mx-auto leading-relaxed">
            Acá vas a encontrar cómo reservar tus camillas, cancelar a tiempo para recuperar tus clases, gestionar tus horarios fijos y comunicarte con nuestro asistente inteligente.
          </p>

          {/* BUSCADOR RÁPIDO */}
          <div className="pt-2 sm:pt-4 max-w-xl mx-auto">
            <div className="relative">
              <Search className="w-5 h-5 text-purple-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                placeholder="Buscá una duda (ej: cancelar, créditos, iPhone, WhatsApp)..."
                className="w-full pl-11 pr-4 py-3 sm:py-3.5 bg-white rounded-2xl border border-purple-200 focus:outline-none focus:ring-2 focus:ring-[#34236F] shadow-sm text-sm sm:text-base placeholder:text-slate-400"
              />
              {searchTerm && (
                <button 
                  onClick={() => setSearchTerm('')}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-purple-600 hover:text-purple-800"
                >
                  Limpiar
                </button>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* TABS DE ACCESO RÁPIDO */}
      <div className="sticky top-16 sm:top-20 z-40 bg-white/95 backdrop-blur-md border-b border-purple-100 py-2.5 px-4 shadow-2xs overflow-x-auto no-scrollbar">
        <div className="max-w-5xl mx-auto flex items-center gap-1.5 sm:gap-2 min-w-max">
          {[
            { id: 'todos', label: 'Todo el manual', icon: Sparkles },
            { id: 'instalacion', label: '1. Instalar App', icon: Smartphone },
            { id: 'reservas', label: '2. Reservar Clases', icon: Calendar },
            { id: 'cancelaciones', label: '3. Cancelar & 24hs', icon: Clock },
            { id: 'fijos', label: '4. Horarios Fijos', icon: Repeat },
            { id: 'planes', label: '5. Planes & Pagos', icon: CreditCard },
            { id: 'whatsapp', label: '6. Asistente IA', icon: MessageSquare },
            { id: 'faq', label: 'Preguntas Frecuentes', icon: HelpCircle },
          ].map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id as any);
                  if (tab.id !== 'todos') {
                    const el = document.getElementById(tab.id);
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  }
                }}
                className={`px-3 py-1.5 rounded-xl text-xs sm:text-sm font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                  active 
                    ? 'bg-[#34236F] text-white shadow-xs' 
                    : 'bg-purple-50/60 text-purple-900 hover:bg-purple-100/70 border border-purple-100'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* CONTENIDO PRINCIPAL EN FORMATO MANUAL / DOCUMENTACIÓN */}
      <main className="max-w-4xl mx-auto px-4 pt-10 sm:pt-14 space-y-16 sm:space-y-24">

        {/* SECCIÓN 1: INSTALACIÓN DE LA APP (PWA) */}
        {(activeTab === 'todos' || activeTab === 'instalacion') && (
          <section id="instalacion" className="scroll-mt-32 space-y-6">
            <div className="border-b border-purple-100 pb-3">
              <span className="text-xs uppercase tracking-widest font-bold text-purple-600 block mb-1">Capítulo 1</span>
              <h2 className="font-serif text-2xl sm:text-3xl font-bold text-[#34236F] flex items-center gap-2.5">
                <Smartphone className="w-7 h-7 text-purple-700" />
                Cómo tener la App de Violett en tu celular
              </h2>
              <p className="text-muted text-sm sm:text-base mt-1">
                Nuestra app es una <b>PWA (Progressive Web App)</b>: no ocupa memoria en tu celular, no necesitás descargar nada de la Play Store ni App Store y podés abrirla en 1 segundo desde tu pantalla de inicio.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* iPhone / iOS */}
              <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm space-y-4">
                <div className="flex items-center gap-3">
                  <span className="w-10 h-10 rounded-xl bg-purple-50 text-purple-800 flex items-center justify-center font-bold text-lg border border-purple-200">
                    
                  </span>
                  <div>
                    <h3 className="font-bold text-base text-foreground">En iPhone o iPad (Safari)</h3>
                    <p className="text-xs text-muted">Instalación en 3 toques</p>
                  </div>
                </div>

                <ol className="space-y-3 text-sm text-slate-700">
                  <li className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-purple-100 text-purple-900 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">1</span>
                    <span>Abrí la página <b>violett.com.ar/pilates</b> en el navegador <b>Safari</b>.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-purple-100 text-purple-900 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">2</span>
                    <span>Tocá el botón <b>Compartir</b> <Share className="inline w-4 h-4 mx-1 text-purple-700" /> en la barra inferior de tu pantalla.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-purple-100 text-purple-900 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">3</span>
                    <span>Deslizá hacia abajo y seleccioná <b>"Agregar a Inicio"</b> (Add to Home Screen).</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-purple-100 text-purple-900 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">4</span>
                    <span>Tocá <b>"Agregar"</b> arriba a la derecha. ¡Listo! Ya tenés el ícono en tu teléfono.</span>
                  </li>
                </ol>
              </div>

              {/* Android */}
              <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm space-y-4">
                <div className="flex items-center gap-3">
                  <span className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-800 flex items-center justify-center font-bold text-lg border border-emerald-200">
                    🤖
                  </span>
                  <div>
                    <h3 className="font-bold text-base text-foreground">En Android (Google Chrome)</h3>
                    <p className="text-xs text-muted">Instalación automática</p>
                  </div>
                </div>

                <ol className="space-y-3 text-sm text-slate-700">
                  <li className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-900 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">1</span>
                    <span>Abrí <b>violett.com.ar/pilates</b> en tu navegador <b>Chrome</b>.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-900 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">2</span>
                    <span>Tocá los <b>tres puntitos (⋮)</b> arriba a la derecha en la esquina superior.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-900 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">3</span>
                    <span>Elegí la opción <b>"Instalar aplicación"</b> o <b>"Agregar a pantalla principal"</b>.</span>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-900 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">4</span>
                    <span>Confirmá la instalación y ya te quedará la app lista como cualquier otra.</span>
                  </li>
                </ol>
              </div>
            </div>
          </section>
        )}

        {/* SECCIÓN 2: RESERVA DE CLASES */}
        {(activeTab === 'todos' || activeTab === 'reservas') && (
          <section id="reservas" className="scroll-mt-32 space-y-6">
            <div className="border-b border-purple-100 pb-3">
              <span className="text-xs uppercase tracking-widest font-bold text-purple-600 block mb-1">Capítulo 2</span>
              <h2 className="font-serif text-2xl sm:text-3xl font-bold text-[#34236F] flex items-center gap-2.5">
                <Calendar className="w-7 h-7 text-purple-700" />
                Cómo Reservar tu Camilla de Pilates Reformer
              </h2>
              <p className="text-muted text-sm sm:text-base mt-1">
                Violett cuenta con un salón boutique con un <b>cupo exclusivo de 3 camillas por turno</b>. Así garantizamos que cada profesora supervise con dedicación tu postura y respiración.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6">
              <h3 className="font-bold text-lg text-foreground flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-500" />
                Paso a paso para agendarte:
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-100 space-y-2">
                  <div className="w-8 h-8 rounded-lg bg-[#34236F] text-white font-bold flex items-center justify-center text-sm">
                    1
                  </div>
                  <h4 className="font-bold text-sm text-[#34236F]">Elegí el día</h4>
                  <p className="text-xs text-muted leading-relaxed">
                    En la pantalla de <b>Inicio</b>, seleccioná el día en la botonera (Hoy, Mañana o los días de la semana).
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-100 space-y-2">
                  <div className="w-8 h-8 rounded-lg bg-[#34236F] text-white font-bold flex items-center justify-center text-sm">
                    2
                  </div>
                  <h4 className="font-bold text-sm text-[#34236F]">Revisá el horario</h4>
                  <p className="text-xs text-muted leading-relaxed">
                    Verás los horarios disponibles y cuántas camillas quedan libres (ej: <i>"3 libres"</i> o <i>"1 libre"</i>).
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-100 space-y-2">
                  <div className="w-8 h-8 rounded-lg bg-[#34236F] text-white font-bold flex items-center justify-center text-sm">
                    3
                  </div>
                  <h4 className="font-bold text-sm text-[#34236F]">Tocá "Reservar"</h4>
                  <p className="text-xs text-muted leading-relaxed">
                    Al confirmar, el sistema descuenta 1 crédito de tu abono y te llega confirmación por WhatsApp y correo.
                  </p>
                </div>
              </div>

              {/* SIMULACIÓN VISUAL DE LOS BADGES */}
              <div className="p-5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  ✦ Qué significan los números en tu pantalla de Inicio:
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    4 créditos disponibles
                  </span>
                  <span className="text-xs text-muted">→ Clases que te quedan libres para agendar en tu mes.</span>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="px-3 py-1.5 rounded-xl bg-purple-50 text-purple-900 border border-purple-200 text-xs font-bold flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-purple-600" />
                    2 clases agendadas
                  </span>
                  <span className="text-xs text-muted">→ Turnos que ya tenés confirmados a futuro (tocá para ver día y hora).</span>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* SECCIÓN 3: CANCELACIONES Y POLÍTICA 24 HORAS */}
        {(activeTab === 'todos' || activeTab === 'cancelaciones') && (
          <section id="cancelaciones" className="scroll-mt-32 space-y-6">
            <div className="border-b border-purple-100 pb-3">
              <span className="text-xs uppercase tracking-widest font-bold text-purple-600 block mb-1">Capítulo 3</span>
              <h2 className="font-serif text-2xl sm:text-3xl font-bold text-[#34236F] flex items-center gap-2.5">
                <Clock className="w-7 h-7 text-purple-700" />
                Política de Cancelaciones y Recuperación de Clases
              </h2>
              <p className="text-muted text-sm sm:text-base mt-1">
                La regla de oro para cuidar la disponibilidad de todas las alumnas del estudio.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="bg-emerald-50/70 border border-emerald-200 rounded-2xl p-6 space-y-3">
                <div className="flex items-center gap-2 text-emerald-800 font-bold text-base">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
                  Con MÁS de 24 hs de anticipación
                </div>
                <p className="text-xs sm:text-sm text-emerald-950 leading-relaxed">
                  Si te surge un imprevisto y avisás con <b>más de 24 horas antes</b> de tu clase:
                </p>
                <ul className="text-xs sm:text-sm text-emerald-900 space-y-2 list-disc pl-5">
                  <li><b>Recuperás tu crédito al instante</b> para usarlo en cualquier otro día del mes.</li>
                  <li>La camilla se libera para que otra compañera pueda aprovechar el horario.</li>
                  <li>Podés cancelar desde la app o pidiéndoselo por WhatsApp al asistente.</li>
                </ul>
              </div>

              <div className="bg-rose-50/70 border border-rose-200 rounded-2xl p-6 space-y-3">
                <div className="flex items-center gap-2 text-rose-800 font-bold text-base">
                  <AlertCircle className="w-6 h-6 text-rose-600 shrink-0" />
                  Con MENOS de 24 hs de anticipación
                </div>
                <p className="text-xs sm:text-sm text-rose-950 leading-relaxed">
                  Si cancelás con <b>menos de 24 horas</b> antes del turno:
                </p>
                <ul className="text-xs sm:text-sm text-rose-900 space-y-2 list-disc pl-5">
                  <li><b>La clase se computa como tomada</b> y no se reintegra el crédito.</li>
                  <li>Esto se debe a que la instructora ya tiene su turno reservado y el cupo quedó bloqueado para vos.</li>
                  <li>Igualmente te agradecemos avisar para que el profesor no te espere en vano.</li>
                </ul>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-5 border border-purple-100 flex items-center justify-between gap-4">
              <div className="space-y-1">
                <h4 className="font-bold text-sm text-[#34236F]">¿Cómo cancelo una clase en la app?</h4>
                <p className="text-xs text-muted">
                  En Inicio, tocá tu botón de <b>"Clases agendadas"</b>, elegí la clase que no vas a poder tomar y seleccioná <b>"Cancelar Reserva"</b>.
                </p>
              </div>
              <Link 
                to="/mis-reservas" 
                className="px-4 py-2 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-900 font-bold text-xs shrink-0 transition-all border border-purple-200"
              >
                Ver Mis Reservas
              </Link>
            </div>
          </section>
        )}

        {/* SECCIÓN 4: HORARIOS FIJOS */}
        {(activeTab === 'todos' || activeTab === 'fijos') && (
          <section id="fijos" className="scroll-mt-32 space-y-6">
            <div className="border-b border-purple-100 pb-3">
              <span className="text-xs uppercase tracking-widest font-bold text-purple-600 block mb-1">Capítulo 4</span>
              <h2 className="font-serif text-2xl sm:text-3xl font-bold text-[#34236F] flex items-center gap-2.5">
                <Repeat className="w-7 h-7 text-purple-700" />
                Horarios Fijos Semanales (Alumnas Recurrentes)
              </h2>
              <p className="text-muted text-sm sm:text-base mt-1">
                La forma más cómoda de no tener que acordarte de reservar cada semana.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-4">
              <div className="flex items-start gap-3">
                <div className="p-3 rounded-xl bg-purple-50 text-purple-800 border border-purple-200 shrink-0">
                  <Repeat className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="font-bold text-base text-foreground">¿Cómo funciona un Horario Fijo?</h3>
                  <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                    Si te coordinás para venir, por ejemplo, todos los <b>Lunes y Miércoles a las 18:00 hs</b>, la administración carga tu horario en el <b>Esquema Fijo</b> del estudio.
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-purple-50/50 border border-purple-100 text-xs sm:text-sm text-purple-950 space-y-2">
                <p>✦ <b>Ventajas de tener Horario Fijo:</b></p>
                <ul className="list-disc pl-5 space-y-1 text-slate-700">
                  <li>Tu camilla está siempre garantizada, sin riesgo de que se llene el horario.</li>
                  <li>El sistema renueva automáticamente tus turnos semana tras semana.</li>
                  <li>Si una semana puntual no podés venir, <b>podés cancelar esa sola clase</b> (con más de 24hs) y usar el crédito recuperado en otro día, sin perder tu horario fijo semanal.</li>
                </ul>
              </div>

              <p className="text-xs text-muted italic">
                * Para solicitar o modificar tu horario fijo, hablá con Débora en la recepción o escribinos por WhatsApp.
              </p>
            </div>
          </section>
        )}

        {/* SECCIÓN 5: PLANES Y PAGOS */}
        {(activeTab === 'todos' || activeTab === 'planes') && (
          <section id="planes" className="scroll-mt-32 space-y-6">
            <div className="border-b border-purple-100 pb-3">
              <span className="text-xs uppercase tracking-widest font-bold text-purple-600 block mb-1">Capítulo 5</span>
              <h2 className="font-serif text-2xl sm:text-3xl font-bold text-[#34236F] flex items-center gap-2.5">
                <CreditCard className="w-7 h-7 text-purple-700" />
                Planes Mensuales, Créditos y Formas de Pago
              </h2>
              <p className="text-muted text-sm sm:text-base mt-1">
                Elegí la frecuencia que mejor se adapte a tu estilo de vida y objetivos corporales.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm space-y-3">
                <span className="text-xs uppercase font-bold text-purple-600 tracking-wider">1 vez por semana</span>
                <h3 className="font-serif text-xl font-bold text-[#34236F]">Plan 4 Clases</h3>
                <p className="text-xs text-muted">Ideal para complementar con otra actividad física o comenzar de a poco.</p>
                <div className="pt-2 text-xs text-slate-600 space-y-1">
                  <p>✓ 4 clases mensuales</p>
                  <p>✓ Ritual de descompresión</p>
                  <p>✓ Vigencia: 30 días</p>
                </div>
              </div>

              <div className="bg-gradient-to-b from-purple-50 to-white rounded-2xl p-6 border-2 border-[#34236F] shadow-md space-y-3 relative">
                <span className="absolute top-3 right-3 text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-[#34236F] text-white">
                  Más Elegido
                </span>
                <span className="text-xs uppercase font-bold text-purple-700 tracking-wider">2 veces por semana</span>
                <h3 className="font-serif text-xl font-bold text-[#34236F]">Plan 8 Clases</h3>
                <p className="text-xs text-muted">El ritmo recomendado para sentir la transformación postural y tono muscular.</p>
                <div className="pt-2 text-xs text-slate-600 space-y-1">
                  <p>✓ 8 clases mensuales</p>
                  <p>✓ Opción de Horario Fijo</p>
                  <p>✓ Vigencia: 30 días</p>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm space-y-3">
                <span className="text-xs uppercase font-bold text-purple-600 tracking-wider">3 veces por semana</span>
                <h3 className="font-serif text-xl font-bold text-[#34236F]">Plan 12 Clases</h3>
                <p className="text-xs text-muted">Máxima constancia, flexibilidad y tonificación profunda.</p>
                <div className="pt-2 text-xs text-slate-600 space-y-1">
                  <p>✓ 12 clases mensuales</p>
                  <p>✓ Opción de Horario Fijo</p>
                  <p>✓ Vigencia: 30 días</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-purple-100 shadow-sm space-y-3">
              <h4 className="font-bold text-sm text-[#34236F]">✦ Cómo abonar tu plan:</h4>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Podés transferir al Alias oficial de Violett Pilates y enviarle la captura del comprobante al asistente de WhatsApp o mostrárselo a Débora en el estudio. Tus créditos se cargan en el momento para que ya puedas reservar.
              </p>
            </div>
          </section>
        )}

        {/* SECCIÓN 6: ASISTENTE DE WHATSAPP INTELIGENTE */}
        {(activeTab === 'todos' || activeTab === 'whatsapp') && (
          <section id="whatsapp" className="scroll-mt-32 space-y-6">
            <div className="border-b border-purple-100 pb-3">
              <span className="text-xs uppercase tracking-widest font-bold text-purple-600 block mb-1">Capítulo 6</span>
              <h2 className="font-serif text-2xl sm:text-3xl font-bold text-[#34236F] flex items-center gap-2.5">
                <MessageSquare className="w-7 h-7 text-[#25D366]" />
                Tu Asistente Inteligente en WhatsApp (24/7)
              </h2>
              <p className="text-muted text-sm sm:text-base mt-1">
                ¿Preferís no entrar a la web? Podés hacer casi todo directamente hablando por WhatsApp.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6">
              <p className="text-sm text-slate-700 leading-relaxed">
                El bot de Violett Pilates entiende lenguaje natural: podés escribirle como a una persona o incluso <b>mandarle un audio de voz</b>.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-100 space-y-1.5">
                  <p className="text-xs font-bold text-purple-900">💬 Consultar tus turnos:</p>
                  <p className="text-xs italic text-slate-600">"Hola, ¿cuándo es mi próxima clase?" o "¿qué clases tengo esta semana?"</p>
                </div>

                <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-100 space-y-1.5">
                  <p className="text-xs font-bold text-purple-900">💬 Ver horarios libres:</p>
                  <p className="text-xs italic text-slate-600">"¿Hay camillas para mañana a la mañana?" o "¿qué turnos hay el viernes?"</p>
                </div>

                <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-100 space-y-1.5">
                  <p className="text-xs font-bold text-purple-900">💬 Reservar un lugar:</p>
                  <p className="text-xs italic text-slate-600">"Anotame en la clase de las 18 hs del miércoles por favor"</p>
                </div>

                <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-100 space-y-1.5">
                  <p className="text-xs font-bold text-purple-900">💬 Cancelar una clase:</p>
                  <p className="text-xs italic text-slate-600">"Cancelame el turno del sábado a las 10 hs"</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200/80 text-xs text-amber-950 flex items-start gap-2.5">
                <Info className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
                <div>
                  <b>Atención personalizada con Débora:</b> Si tenés un pedido especial que el asistente no puede resolver, te avisará con amabilidad para que puedas coordinarlo directamente con Débora en el estudio.
                </div>
              </div>
            </div>
          </section>
        )}

        {/* SECCIÓN 7: PREGUNTAS FRECUENTES (FAQ) */}
        {(activeTab === 'todos' || activeTab === 'faq') && (
          <section id="faq" className="scroll-mt-32 space-y-6">
            <div className="border-b border-purple-100 pb-3">
              <span className="text-xs uppercase tracking-widest font-bold text-purple-600 block mb-1">Capítulo 7</span>
              <h2 className="font-serif text-2xl sm:text-3xl font-bold text-[#34236F] flex items-center gap-2.5">
                <HelpCircle className="w-7 h-7 text-purple-700" />
                Preguntas Frecuentes
              </h2>
              <p className="text-muted text-sm sm:text-base mt-1">
                Respuestas inmediatas a las dudas más habituales de nuestras alumnas.
              </p>
            </div>

            <div className="space-y-3">
              {filteredFaqs.map((faq, idx) => {
                const isOpen = expandedFaq === idx;
                return (
                  <div 
                    key={idx}
                    className="bg-white rounded-2xl border border-purple-100 shadow-2xs overflow-hidden transition-all"
                  >
                    <button
                      type="button"
                      onClick={() => toggleFaq(idx)}
                      className="w-full text-left p-5 flex items-center justify-between gap-4 font-bold text-sm sm:text-base text-foreground hover:bg-purple-50/40 transition-colors cursor-pointer"
                    >
                      <span className="flex items-center gap-2.5">
                        <span className="w-2 h-2 rounded-full bg-purple-400 shrink-0" />
                        {faq.pregunta}
                      </span>
                      <ChevronDown className={`w-5 h-5 text-purple-400 shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
                    </button>

                    <AnimatePresence>
                      {isOpen && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden px-5 pb-5 pt-1 text-xs sm:text-sm text-slate-600 border-t border-purple-50 leading-relaxed"
                        >
                          {faq.respuesta}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}

              {filteredFaqs.length === 0 && (
                <div className="text-center py-12 bg-white rounded-2xl border border-dashed border-purple-200 p-6 space-y-2">
                  <p className="text-muted text-sm">No encontramos resultados para tu búsqueda "{searchTerm}".</p>
                  <button 
                    onClick={() => { setSearchTerm(''); setActiveTab('todos'); }}
                    className="text-xs font-bold text-[#34236F] hover:underline"
                  >
                    Ver todas las preguntas frecuentes
                  </button>
                </div>
              )}
            </div>
          </section>
        )}

        {/* BANNER FINAL DE ASISTENCIA Y CONTACTO */}
        <section className="bg-gradient-to-br from-[#34236F] to-[#25154D] rounded-3xl p-8 sm:p-12 text-white text-center space-y-6 shadow-xl relative overflow-hidden">
          <div className="space-y-3 max-w-xl mx-auto">
            <h3 className="font-serif text-2xl sm:text-4xl font-bold">
              ¿Tenés alguna otra duda?
            </h3>
            <p className="text-purple-200 text-sm sm:text-base leading-relaxed">
              Estamos en el estudio para acompañarte en cada movimiento. Escribinos o acercate a la recepción con Débora.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <a
              href="https://wa.me/5491157691786"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-3 rounded-xl bg-[#25D366] hover:bg-[#20BA5A] text-white font-bold text-sm shadow-md flex items-center gap-2 transition-all cursor-pointer"
            >
              <MessageSquare className="w-5 h-5" />
              Escribir por WhatsApp
            </a>
            <Link
              to="/"
              className="px-6 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-sm border border-white/20 transition-all cursor-pointer"
            >
              Ir a Mi Panel de Alumna
            </Link>
          </div>
        </section>

      </main>

      {/* FOOTER */}
      <footer className="mt-20 pt-8 border-t border-purple-100 text-center text-xs text-muted space-y-2">
        <p className="font-serif text-sm font-semibold text-purple-900">Violett Pilates Boutique ✦</p>
        <p>© {new Date().getFullYear()} Todos los derechos reservados. Diseñado para tu bienestar.</p>
        <div className="flex justify-center gap-4 pt-1">
          <Link to="/terminos" className="hover:underline">Términos y Condiciones</Link>
          <span>•</span>
          <Link to="/privacidad" className="hover:underline">Política de Privacidad</Link>
          <span>•</span>
          <Link to="/eliminar-datos" className="hover:underline">Gestión de Datos</Link>
        </div>
      </footer>

    </div>
  );
}
