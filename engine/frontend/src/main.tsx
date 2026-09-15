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

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
