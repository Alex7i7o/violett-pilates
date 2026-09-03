import React from 'react';

export function Footer() {
  return (
    <footer className="bg-primary-main pt-16 pb-8 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
        <div>
          <img src="/isotipo.png" alt="Violett" className="h-12 w-auto mb-6 brightness-0 invert opacity-90" />
          <p className="text-primary-light/80 text-sm leading-relaxed max-w-xs">
            <strong>Salud, Belleza & Recuperación Integral.</strong><br/>
            Más de 10 años brindando excelencia en cuidado corporal y postoperatorio.
          </p>
        </div>
        
        <div>
          <h4 className="text-white font-bold mb-6">Enlaces Rápidos</h4>
          <ul className="space-y-3 text-primary-light/80 text-sm">
            <li><a href="#tratamientos" className="hover:text-white transition-colors">Tratamientos</a></li>
            <li><a href="#tratamientos" className="hover:text-white transition-colors">Precios y Módulos</a></li>
            <li><a href="#medicos" className="hover:text-white transition-colors">Derivaciones Médicas</a></li>
            <li><a href="#contacto" className="hover:text-white transition-colors">Ubicación en San Justo</a></li>
          </ul>
        </div>
        
        <div>
          <h4 className="text-white font-bold mb-6">Contacto Directo</h4>
          <ul className="space-y-3 text-primary-light/80 text-sm">
            <li>WhatsApp: <a href="https://wa.me/5491164142172" className="hover:text-white transition-colors">+54 9 11 6414-2172</a></li>
            <li>Instagram: <a href="https://instagram.com/violett.estetica" className="hover:text-white transition-colors">@violett.estetica</a></li>
            <li>Web oficial: <a href="https://www.violett.com.ar" className="hover:text-white transition-colors">www.violett.com.ar</a></li>
          </ul>
        </div>
      </div>
      
      <div className="max-w-6xl mx-auto pt-8 border-t border-white/10 text-center">
        <p className="text-primary-light/40 text-xs">
          © {new Date().getFullYear()} Violett Estética. Todos los derechos reservados. Tratamientos estéticos y complementarios no invasivos.
        </p>
      </div>
    </footer>
  );
}
