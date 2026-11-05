import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';

import { ClientConfigProvider } from './context/ClientConfigContext';
import { BookingRoutes } from './routes/BookingRoutes';
import { Terminos } from './pages/public/Terminos';
import { Privacidad } from './pages/public/Privacidad';
import { EliminarDatos } from './pages/public/EliminarDatos';
import { TutorialDoc } from './pages/public/TutorialDoc';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ClientConfigProvider>
        <BrowserRouter basename={import.meta.env.BASE_URL}>
          <Toaster position="top-right" richColors />
          <Routes>
            <Route path="/terminos" element={<Terminos />} />
            <Route path="/privacidad" element={<Privacidad />} />
            <Route path="/eliminar-datos" element={<EliminarDatos />} />
            <Route path="/data-deletion" element={<EliminarDatos />} />
            <Route path="/instrucciones-eliminacion-datos" element={<EliminarDatos />} />
            <Route path="/doc" element={<TutorialDoc />} />
            <Route path="/tutorial" element={<TutorialDoc />} />
            <Route path="/guia" element={<TutorialDoc />} />
            <Route path="/*" element={<BookingRoutes />} />
          </Routes>
        </BrowserRouter>
      </ClientConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
