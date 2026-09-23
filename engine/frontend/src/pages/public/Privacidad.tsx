import React from 'react';

export function Privacidad() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-3xl mx-auto bg-white p-8 rounded-2xl shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Política de Privacidad</h1>
        <div className="prose text-gray-600">
          <p className="mb-4">Tu privacidad es importante para nosotros. Cumplimos con la Ley de Protección de Datos Personales (Ley 25.326 de Argentina).</p>
          
          <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">1. Datos Recopilados</h2>
          <p className="mb-4">Recopilamos tu nombre, correo electrónico, número de teléfono y, de ser necesario, información médica básica requerida para tu seguridad física durante las clases.</p>

          <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">2. Uso de la Información</h2>
          <p className="mb-4">Utilizamos tus datos para gestionar tus reservas, contactarte vía WhatsApp o email por cancelaciones o alertas de cupo, y procesar tus pagos de membresías.</p>

          <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">3. Derechos ARCO</h2>
          <p className="mb-4">Tienes derecho a solicitar el Acceso, Rectificación, Actualización o Supresión de tus datos personales en nuestra base de datos. Para ejercerlos, contacta a nuestro soporte.</p>

          <h2 className="text-xl font-semibold text-gray-800 mt-6 mb-3">4. Cookies de Autenticación</h2>
          <p className="mb-4">Esta plataforma utiliza cookies estrictamente necesarias (tokens de sesión) para mantenerte logueado de forma segura.</p>
        </div>
      </div>
    </div>
  );
}
