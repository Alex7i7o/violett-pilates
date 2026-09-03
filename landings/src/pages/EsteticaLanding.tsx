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
