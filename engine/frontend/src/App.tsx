/* Developed by FireSeed - Fueling Innovation */
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';

import { ClientConfigProvider } from './context/ClientConfigContext';
import { BookingRoutes } from './routes/BookingRoutes';

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
            {/* 
              Aquí, el día de mañana, se puede interceptar la Landing Page,
              ej: <Route path="/" element={<LandingPage />} />
              y mover BookingRoutes a "/app/*".
            */}
            <Route path="/*" element={<BookingRoutes />} />
          </Routes>
        </BrowserRouter>
      </ClientConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
