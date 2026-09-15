import React from 'react';
import { Header } from '../components/estetica/Header';
import { Hero } from '../components/estetica/Hero';
import { Credibility } from '../components/estetica/Credibility';
import { DeboraZarate } from '../components/estetica/DeboraZarate';
import { Treatments } from '../components/estetica/Treatments';
import { Doctors } from '../components/estetica/Doctors';
import { Testimonials } from '../components/estetica/Testimonials';
import { FAQ } from '../components/estetica/FAQ';
import { Contact } from '../components/estetica/Contact';
import { Footer } from '../components/estetica/Footer';
import { ScrollToTop } from '../components/estetica/ScrollToTop';

export default function EsteticaLanding() {
  React.useEffect(() => {
    document.title = "Violett Estética";
    
    const updateFavicon = (isDark: boolean) => {
      let link = document.querySelector("link[rel~='icon']") as HTMLLinkElement;
      if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
      }
      // Si el usuario quiere uno oscuro para estética, puede crear 'logo-estetica-icon-dark.png'
      // Por defecto usamos el mismo si no existe, o definimos el nombre para que lo suban:
      link.href = isDark ? '/logo-estetica-icon-dark.png' : '/logo-estetica-icon.png';
    };

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    updateFavicon(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => updateFavicon(e.matches);
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <ScrollToTop />
      <main>
        <Hero />
        <Credibility />
        <DeboraZarate />
        <Treatments />
        <Doctors />
        <Testimonials />
        <div id="faq"><FAQ /></div>
        <Contact />
      </main>
      <Footer />
    </div>
  );
}
