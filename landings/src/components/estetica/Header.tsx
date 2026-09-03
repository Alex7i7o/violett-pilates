import React, { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [activeTab, setActiveTab] = useState('');

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const links = [
    { label: "Servicios", href: "#tratamientos" },
    { label: "Área Médica", href: "#medicos" },
    { label: "Casos de Éxito", href: "#testimonios" },
    { label: "FAQ", href: "#faq" }
  ];

  return (
    <>
      <div className="bg-primary-main text-white py-2 px-4 text-center text-xs sm:text-sm font-medium">
        📍 Comisionado Indart 2822, San Justo • Atención con turno previo • 
        <a href="https://wa.me/5491164142172" target="_blank" rel="noopener noreferrer" className="ml-1 underline hover:text-accent-gold transition-colors">WhatsApp: +54 9 11 6414-2172</a>
      </div>
      
      <header className={`sticky top-0 z-50 transition-all duration-300 border-b border-primary-main ${scrolled ? 'bg-white/80 backdrop-blur-md shadow-sm py-3' : 'bg-transparent py-5'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between">
          <a href="#" className="flex items-center gap-2">
            <img src="/logotipo.png" alt="Violett Estética" className="h-14 sm:h-16 w-auto object-contain" />
          </a>
          
          <nav className="hidden lg:flex items-center gap-2">
            {links.map((l, i) => {
              const isActive = activeTab === l.href;
              return (
                <a 
                  key={i} 
                  href={l.href}
                  onClick={() => setActiveTab(l.href)}
                  className={`relative px-4 py-2 text-sm font-semibold transition-colors duration-300 ${isActive ? 'text-white' : 'text-foreground hover:text-primary-main'}`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="active-nav-pill"
                      className="absolute inset-0 bg-primary-main rounded-xl shadow-inner"
                      initial={false}
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                      style={{ originY: "0px" }}
                    />
                  )}
                  <span className="relative z-10">{l.label}</span>
                </a>
              );
            })}
            <a href="#contacto" className="ml-4 px-5 py-2.5 rounded-xl bg-primary-main text-white text-sm font-bold hover:bg-primary-hover shadow-sm transition-transform active:scale-95">
              Reservar Turno
            </a>
          </nav>

          <button className="lg:hidden p-2 text-foreground" onClick={() => setMobileMenu(true)}>
            <Menu className="w-6 h-6" />
          </button>
        </div>
      </header>

      <AnimatePresence>
        {mobileMenu && (
          <motion.div 
            initial={{ opacity: 0, x: '100%' }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: '100%' }}
            transition={{ type: 'spring', bounce: 0, duration: 0.4 }}
            className="fixed inset-0 z-[60] bg-white flex flex-col pt-safe"
          >
            <div className="flex items-center justify-between p-4 border-b border-primary-light">
              <img src="/logotipo.png" alt="Violett" className="h-12 w-auto object-contain" />
              <button onClick={() => setMobileMenu(false)} className="p-2 text-foreground bg-background rounded-full">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="flex-1 flex flex-col p-6 gap-6 overflow-y-auto">
              {links.map((l, i) => (
                <a 
                  key={i} 
                  href={l.href} 
                  onClick={() => {
                    setActiveTab(l.href);
                    setMobileMenu(false);
                  }} 
                  className={`text-xl font-bold border-b border-primary-light pb-4 ${activeTab === l.href ? 'text-primary-main' : 'text-foreground'}`}
                >
                  {l.label}
                </a>
              ))}
            </div>
            <div className="p-6 pb-safe border-t border-primary-light bg-background">
              <a href="#contacto" onClick={() => setMobileMenu(false)} className="w-full py-4 rounded-xl flex items-center justify-center bg-primary-main text-white font-bold text-lg shadow-sm">
                Reservar Turno
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
