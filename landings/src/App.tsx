import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomeLanding from './pages/HomeLanding';
import PilatesLanding from './pages/PilatesLanding';
import EsteticaLanding from './pages/EsteticaLanding';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Redirección temporal a estética como pediste */}
        <Route path="/" element={<Navigate to="/estetica" replace />} />
        
        {/* Rutas reales (Home queda accesible si vas a /home o quitamos el redirect luego) */}
        <Route path="/home" element={<HomeLanding />} />
        <Route path="/pilates" element={<PilatesLanding />} />
        <Route path="/estetica" element={<EsteticaLanding />} />
        
        {/* Ruta comodín para capturar cualquier ruta inexistente (como /login) y enviarla a estética */}
        <Route path="*" element={<Navigate to="/estetica" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
