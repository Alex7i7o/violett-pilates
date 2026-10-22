import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  ShieldCheck, 
  Trash2, 
  ArrowLeft, 
  CheckCircle2, 
  AlertCircle, 
  ExternalLink, 
  FileText, 
  Mail, 
  Phone, 
  Clock, 
  Database
} from 'lucide-react';
import axios from 'axios';

export function EliminarDatos() {
  const [searchParams] = useSearchParams();
  const codeParam = searchParams.get('code') || searchParams.get('id');

  const [email, setEmail] = useState('');
  const [telefono, setTelefono] = useState('');
  const [motivo, setMotivo] = useState('');
  const [loading, setLoading] = useState(false);
  const [successCode, setSuccessCode] = useState<string | null>(codeParam);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Si viene con un código por URL (por ejemplo el generado por el callback de Meta), consultar estado
  useEffect(() => {
    if (codeParam) {
      axios.get(`/api/eliminar-datos/?code=${encodeURIComponent(codeParam)}`)
        .then(res => {
          setSuccessMessage(res.data.mensaje || `Tu solicitud #${codeParam} está registrada.`);
        })
        .catch(() => {
          setSuccessMessage(`Solicitud de eliminación registrada con código de seguimiento #${codeParam}.`);
        });
    }
  }, [codeParam]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setLoading(true);

    try {
      const response = await axios.post('/api/eliminar-datos/solicitar/', {
        email,
        telefono,
        motivo,
      });

      setSuccessCode(response.data.codigo_confirmacion);
      setSuccessMessage(response.data.mensaje);
      setEmail('');
      setTelefono('');
      setMotivo('');
    } catch (err: any) {
      const detail = err.response?.data?.error || 'No se pudo procesar la solicitud. Por favor verificá los datos o contactanos por WhatsApp.';
      setErrorMessage(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Botón Volver */}
        <div className="mb-6">
          <Link 
            to="/" 
            className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-[#34236F] transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver al inicio
          </Link>
        </div>

        {/* Tarjeta Principal */}
        <div className="bg-white rounded-3xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Cabecera */}
          <div className="bg-[#34236F] text-white px-8 py-10">
            <div className="flex items-center gap-3 mb-3">
              <span className="p-2 bg-white/10 rounded-xl backdrop-blur-sm">
                <ShieldCheck className="w-6 h-6 text-pink-200" />
              </span>
              <span className="text-xs uppercase tracking-wider font-semibold text-pink-200 bg-white/10 px-3 py-1 rounded-full">
                Cumplimiento Meta & Ley 25.326
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Instrucciones para la Eliminación de Datos de Usuario
            </h1>
            <p className="mt-2 text-sm sm:text-base text-gray-200">
              Violett Pilates • Conforme a las Políticas de la Plataforma Meta y el Derecho de Supresión (Habeas Data).
            </p>
          </div>

          <div className="p-6 sm:p-10 space-y-10 text-gray-700 leading-relaxed">
            {/* Introducción */}
            <div className="bg-purple-50/50 rounded-2xl p-5 border border-purple-100/80">
              <p className="text-sm sm:text-base text-[#2B1A53]">
                En <strong>Violett Pilates</strong> respetamos tu privacidad y tu derecho al control absoluto de tu información personal. 
                Si utilizaste el inicio de sesión con <strong>Facebook</strong>, interactuaste con nuestro asistente de <strong>WhatsApp Business</strong>, 
                o creaste una cuenta en nuestra plataforma de reservas, podés solicitar la eliminación permanente de todos tus datos en cualquier momento.
              </p>
            </div>

            {/* Aviso si viene con código de confirmación por URL */}
            {successCode && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-5 flex items-start gap-4">
                <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-emerald-900">
                    Solicitud de Eliminación Confirmada
                  </h3>
                  <p className="text-sm text-emerald-700 mt-1">
                    {successMessage || 'Tu solicitud fue registrada con éxito en nuestros servidores.'}
                  </p>
                  <div className="mt-2 text-xs font-mono bg-white inline-block px-3 py-1 rounded-lg border border-emerald-200 text-emerald-800">
                    Código de seguimiento: <strong>{successCode}</strong>
                  </div>
                </div>
              </div>
            )}

            {/* OPCION 1: Pasos para eliminar desde Facebook */}
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#34236F] text-white flex items-center justify-center font-bold text-sm">
                  1
                </div>
                <h2 className="text-xl font-bold text-gray-900">
                  Cómo revocar permisos y eliminar datos desde Facebook / Meta
                </h2>
              </div>
              <p className="text-sm text-gray-600">
                Si iniciaste sesión a través de Facebook o Meta, podés remover la aplicación y solicitar el borrado automático de tus datos siguiendo estos pasos:
              </p>

              <div className="grid sm:grid-cols-2 gap-4 mt-3">
                <div className="bg-gray-50 p-4 rounded-2xl border border-gray-100">
                  <span className="font-bold text-[#34236F] text-sm block mb-1">Paso 1: Configuración</span>
                  <p className="text-xs text-gray-600">
                    Ingresá a tu cuenta de Facebook, tocá tu foto de perfil arriba a la derecha y seleccioná <strong>Configuración y privacidad</strong> &gt; <strong>Configuración</strong>.
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-2xl border border-gray-100">
                  <span className="font-bold text-[#34236F] text-sm block mb-1">Paso 2: Apps y sitios web</span>
                  <p className="text-xs text-gray-600">
                    En el menú lateral izquierdo, hacé clic en <strong>Apps y sitios web</strong> para ver todas las aplicaciones vinculadas a tu cuenta.
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-2xl border border-gray-100">
                  <span className="font-bold text-[#34236F] text-sm block mb-1">Paso 3: Seleccionar Violett</span>
                  <p className="text-xs text-gray-600">
                    Buscá <strong>Violett Pilates</strong> (o Violett) en el listado de aplicaciones activas.
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-2xl border border-gray-100">
                  <span className="font-bold text-[#34236F] text-sm block mb-1">Paso 4: Confirmar eliminación</span>
                  <p className="text-xs text-gray-600">
                    Hacé clic en <strong>Eliminar</strong>. Marcá la casilla para solicitar que la app elimine tus datos y confirmá la acción.
                  </p>
                </div>
              </div>
            </section>

            {/* OPCION 2: Formulario de solicitud web directa */}
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[#34236F] text-white flex items-center justify-center font-bold text-sm">
                  2
                </div>
                <h2 className="text-xl font-bold text-gray-900">
                  Solicitud directa de eliminación de cuenta y datos
                </h2>
              </div>
              <p className="text-sm text-gray-600">
                Podés ingresar tu correo electrónico o tu número de teléfono para que nuestro sistema elimine de forma permanente tu registro en nuestra base de datos:
              </p>

              <form onSubmit={handleSubmit} className="bg-gray-50 p-6 rounded-2xl border border-gray-200 space-y-4">
                {errorMessage && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-sm text-red-700">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{errorMessage}</span>
                  </div>
                )}

                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Correo Electrónico Registrado
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="tu@email.com"
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#34236F] text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Número de WhatsApp / Teléfono
                    </label>
                    <input
                      type="tel"
                      value={telefono}
                      onChange={(e) => setTelefono(e.target.value)}
                      placeholder="Ej: 11 6414-2172"
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#34236F] text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Motivo (Opcional)
                  </label>
                  <textarea
                    rows={2}
                    value={motivo}
                    onChange={(e) => setMotivo(e.target.value)}
                    placeholder="Contanos brevemente el motivo de tu solicitud o alguna indicación especial..."
                    className="w-full px-4 py-2 rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#34236F] text-sm"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-medium rounded-xl text-sm transition-colors flex items-center gap-2 shadow-sm disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                    {loading ? 'Enviando solicitud...' : 'Solicitar Eliminación de Datos'}
                  </button>
                </div>
              </form>
            </section>

            {/* ¿Qué datos se eliminan? */}
            <section className="space-y-4">
              <div className="flex items-center gap-2 text-gray-900 font-bold text-lg">
                <Database className="w-5 h-5 text-[#34236F]" />
                <h3>¿Qué información eliminamos de forma permanente?</h3>
              </div>
              
              <div className="grid sm:grid-cols-2 gap-3 text-sm text-gray-600">
                <div className="flex items-start gap-2">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span><strong>Perfil de Usuario:</strong> Nombre, apellido, email, teléfono y foto de perfil.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span><strong>Reservas y Grilla:</strong> Turnos agendados, asistencias y cancelaciones históricas.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span><strong>Mensajes de WhatsApp:</strong> Conversaciones, audios y transcripciones con el asistente.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span><strong>Fichas Médicas:</strong> Registro de lesiones y formularios de salud preventiva.</span>
                </div>
              </div>

              <p className="text-xs text-gray-500 italic mt-2">
                * Nota: Ciertos registros fiscales o de comprobantes de pago emitidos pueden conservarse de forma anónima durante el período estrictamente obligatorio estipulado por las normativas tributarias vigentes (AFIP).
              </p>
            </section>

            {/* Plazos y Contacto */}
            <div className="border-t border-gray-200 pt-8 grid sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-gray-900 font-semibold text-sm">
                  <Clock className="w-4 h-4 text-[#34236F]" />
                  <span>Plazos de Procesamiento</span>
                </div>
                <p className="text-xs text-gray-600">
                  Las solicitudes son procesadas dentro de un plazo de <strong>24 a 48 horas hábiles</strong>. Te notificaremos por correo o mensaje una vez completada la purga.
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-gray-900 font-semibold text-sm">
                  <Mail className="w-4 h-4 text-[#34236F]" />
                  <span>Contacto de Privacidad</span>
                </div>
                <p className="text-xs text-gray-600">
                  Responsable: Débora Zárate (Violett Pilates)<br />
                  Gral. Guido 1573, Ramos Mejía, Buenos Aires.<br />
                  WhatsApp: <a href="https://wa.me/5491164142172" target="_blank" rel="noopener noreferrer" className="text-[#34236F] underline">+54 9 11 6414-2172</a>
                </p>
              </div>
            </div>

            {/* Enlaces Legales */}
            <div className="border-t border-gray-100 pt-6 flex flex-wrap gap-4 text-xs text-gray-500 justify-between items-center">
              <span>© {new Date().getFullYear()} Violett Pilates. Todos los derechos reservados.</span>
              <div className="flex gap-4">
                <Link to="/privacidad" className="hover:text-[#34236F] underline">
                  Política de Privacidad
                </Link>
                <Link to="/terminos" className="hover:text-[#34236F] underline">
                  Términos y Condiciones
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
