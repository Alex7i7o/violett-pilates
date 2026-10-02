import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';

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
    transition: { staggerChildren: 0.1, delayChildren: 0.1 }
  }
};

export function ResenasView() {
  const { data: resenas = [], isLoading } = useQuery({
    queryKey: ['resenas_public_all'],
    queryFn: async () => {
      try {
        const res = await api.get('/resenas/resenas/');
        return res.data;
      } catch (err) {
        console.error(err);
        return [];
      }
    }
  });

  return (
    <div className="min-h-screen bg-background text-primary-main font-sans selection:bg-primary-main selection:text-white pb-20">
      <header className="py-6 px-4 md:px-6 max-w-7xl mx-auto flex justify-between items-center">
        <Link to="/">
          <img src="/logo-full.png" alt="Violett Pilates" className="h-8 md:h-10 object-contain" />
        </Link>
        <Link 
          to="/" 
          className="px-6 py-2.5 rounded-full bg-primary-main/10 text-primary-main font-semibold hover:bg-primary-main hover:text-white transition-all duration-300"
        >
          Volver al inicio
        </Link>
      </header>

      <motion.main 
        initial="hidden" 
        animate="visible" 
        variants={staggerContainer}
        className="max-w-4xl mx-auto px-4 md:px-6 pt-12 md:pt-20"
      >
        <motion.h1 variants={fadeUp} className="font-marcellus text-4xl md:text-5xl mb-6 text-center text-primary-main">
          Ecos de nuestra comunidad
        </motion.h1>
        <motion.p variants={fadeUp} className="font-sans text-center text-base md:text-lg mb-14 opacity-80 text-violett-800">
          Descubrí las experiencias de quienes ya hicieron de la elegancia y el bienestar su estilo de vida diario.
        </motion.p>

        {isLoading ? (
          <div className="flex justify-center my-20">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-main"></div>
          </div>
        ) : (
          <div className="grid gap-6 md:gap-8">
            {resenas.length > 0 ? (
              resenas.map((resena: any, i: number) => (
                <motion.blockquote key={i} variants={fadeUp} className="p-6 md:p-8 bg-white rounded-3xl shadow-sm border border-primary-main/5 relative hover:shadow-md transition-shadow">
                  <div className="absolute top-4 left-4 text-4xl text-violett-200 font-serif">"</div>
                  <div className="flex mb-4 relative z-10 justify-end">
                    {[...Array(5)].map((_, idx) => (
                      <span key={idx} className={idx < resena.estrellas ? "text-yellow-400 text-lg" : "text-gray-200 text-lg"}>★</span>
                    ))}
                  </div>
                  <p className="italic text-base md:text-lg mb-6 leading-relaxed opacity-80 relative z-10">
                    {resena.mensaje}
                  </p>
                  <footer className="font-bold text-violett-700 text-sm md:text-base">— {resena.usuario?.first_name || 'Alumna'} {resena.usuario?.last_name || ''}</footer>
                </motion.blockquote>
              ))
            ) : (
              <motion.div variants={fadeUp} className="text-center text-primary-main/60 py-10">
                Aún no hay reseñas publicadas.
              </motion.div>
            )}
          </div>
        )}

        <motion.div variants={fadeUp} className="mt-16 flex justify-center">
          <Link 
            to="/" 
            className="inline-flex items-center justify-center bg-primary-main text-white font-sans font-medium px-8 py-3.5 md:px-10 md:py-4 rounded-full hover:bg-violett-700 hover:scale-[1.02] active:scale-95 transition-all duration-300 shadow-xl shadow-primary-main/20 text-sm md:text-base"
          >
            Volver al inicio
          </Link>
        </motion.div>
      </motion.main>
    </div>
  );
}
