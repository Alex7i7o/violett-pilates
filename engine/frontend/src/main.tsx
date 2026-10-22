console.log(
  "%c🚀 Welcome to FireSeed - Fueling Innovation",
  "color: #fff; background: #2A1C5A; padding: 10px; border-radius: 8px; font-size: 14px; font-weight: bold;"
);

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

window.addEventListener('pageshow', (event) => {
  if (event.persisted) {
    window.location.reload();
  }
});

// Manejo inteligente de actualizacion de chunks dinamicos tras un nuevo deploy
window.addEventListener('vite:preloadError', (event) => {
  console.warn('[Vite] Chunk dinamico desactualizado. Recargando bundle...', event);
  window.location.reload();
});

window.addEventListener('error', (event) => {
  const msg = event?.message || '';
  if (
    msg.includes('Failed to fetch dynamically imported module') ||
    msg.includes('Importing a module script failed') ||
    msg.includes('error loading dynamically imported module')
  ) {
    const lastReload = sessionStorage.getItem('last_chunk_reload');
    const now = Date.now();
    if (!lastReload || now - parseInt(lastReload, 10) > 10000) {
      sessionStorage.setItem('last_chunk_reload', now.toString());
      console.warn('[SPA] Modulo no encontrado tras deploy. Recargando...');
      window.location.reload();
    }
  }
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
