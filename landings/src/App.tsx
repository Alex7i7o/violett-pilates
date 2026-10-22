import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomeLanding from './pages/HomeLanding';
import PilatesLanding from './pages/PilatesLanding';
import EsteticaLanding from './pages/EsteticaLanding';
import EliminarDatos from './pages/EliminarDatos';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Redirección temporal a estética como pediste */}
        <Route path="/" element={<Navigate to="/estetica" replace />} />
        
        {/* Rutas reales */}
        <Route path="/home" element={<HomeLanding />} />
        <Route path="/pilates" element={<PilatesLanding />} />
        <Route path="/estetica" element={<EsteticaLanding />} />
        
        {/* Rutas legales requeridas por Meta */}
        <Route path="/eliminar-datos" element={<EliminarDatos />} />
        <Route path="/data-deletion" element={<EliminarDatos />} />
        <Route path="/instrucciones-eliminacion-datos" element={<EliminarDatos />} />
        
        {/* Ruta comodín para capturar cualquier ruta inexistente y enviarla a estética */}
        <Route path="*" element={<Navigate to="/estetica" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
