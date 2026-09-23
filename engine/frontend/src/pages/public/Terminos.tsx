import React from 'react';

export function Terminos() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-3xl mx-auto bg-white p-8 rounded-2xl shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Términos y Condiciones</h1>
        <div className="prose text-gray-600">
          <p className="mb-4">Bienvenido a nuestro sistema de reservas. Al utilizar esta plataforma, aceptas los siguientes términos:</p>
          
          <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">1. Uso del Servicio</h2>
          <p className="mb-4">Esta plataforma permite la gestión de reservas, pagos y membresías para nuestros servicios físicos.</p>

          <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">2. Política de Cancelación</h2>
          <p className="mb-4">Las reservas de clases deben cancelarse con una antelación mínima de 24 horas. De no ser así, el crédito de la clase se considerará consumido y no será devuelto.</p>

          <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">3. Pagos y Reembolsos</h2>
          <p className="mb-4">Los planes y membresías adquiridos no son reembolsables una vez activados, salvo excepciones expresamente autorizadas por la administración.</p>

          <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">4. Exención de Responsabilidad</h2>
          <p className="mb-4">Al asistir a las clases, declaras estar en condiciones físicas aptas. El estudio no se responsabiliza por lesiones derivadas de condiciones preexistentes o por no seguir las instrucciones de los profesionales.</p>
        </div>
      </div>
    </div>
  );
}
