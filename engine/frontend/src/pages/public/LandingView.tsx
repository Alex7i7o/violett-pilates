import React from 'react';
import { Link } from 'react-router-dom';

export function LandingView() {
  return (
    <div className="min-h-screen bg-background text-primary-main font-sans">
      {/* Hero Section */}
      <header className="flex flex-col items-center justify-center text-center py-24 px-6">
        <h1 className="font-laluxes text-5xl md:text-7xl mb-6">Violett ✦ Pilates</h1>
        <h2 className="font-marcellus text-2xl md:text-4xl max-w-3xl mb-8 leading-snug">
          ✦ El arte de esculpir la silueta de tus sueños y habitar tu cuerpo con elegancia
        </h2>
        <p className="font-sans text-lg md:text-xl font-bold mb-6">
          El estudio boutique de Pilates Reformer exclusivo en Ramos Mejía.
        </p>
        <p className="font-sans max-w-2xl text-base md:text-lg mb-10 opacity-90 leading-relaxed">
          Lejos del ruido del mundo, existe un espacio donde el tiempo parece detenerse. Un lugar impecable, envuelto en una suave fragancia floral, diseñado para la mujer que elige dedicarse tiempo a sí misma con sofisticación. En Violett, el entrenamiento físico se transforma en una expresión de belleza. Es una pausa delicada donde cada respiración y cada movimiento en el Reformer te acercan a esa figura armónica que deseás, mientras tu mente encuentra una serenidad absoluta.
        </p>
        <Link 
          to="/login"
          className="inline-block bg-primary-main text-white font-sans font-medium px-8 py-4 rounded hover:opacity-90 transition-opacity"
        >
          ✦ Descubrir mi espacio
        </Link>
      </header>

      {/* Section 2 */}
      <section className="py-20 px-6 max-w-4xl mx-auto text-center border-t border-primary-main/20">
        <h2 className="font-marcellus text-3xl mb-6">✦ Una vitalidad radiante para vivir al máximo</h2>
        <p className="font-sans mb-4 leading-relaxed opacity-90">
          El cuerpo es el lienzo de nuestra historia, y está diseñado para moverse con libertad, agilidad y gracia. Entendemos que el verdadero lujo es sentirte plena, ligera y sin tensiones en cada paso que das.
        </p>
        <p className="font-sans leading-relaxed opacity-90">
          A través de movimientos fluidos y precisos en el Reformer, despertamos la memoria de tus músculos. No solo restauramos esa elasticidad que creías olvidada y aliviamos las molestias diarias, sino que encendemos una energía vibrante para que disfrutes tu juventud al máximo. Es el secreto de una belleza que se refleja en la firmeza de tu cuerpo y en la soltura con la que abrazás cada día.
        </p>
      </section>

      {/* Section 3 */}
      <section className="py-20 px-6 max-w-4xl mx-auto text-center border-t border-primary-main/20">
        <h2 className="font-marcellus text-3xl mb-6">✦ Te esperamos exactamente como sos</h2>
        <p className="font-sans leading-relaxed opacity-90">
          No necesitás experiencia previa ni cumplir con estándares irreales para cruzar nuestra puerta. Este es un espacio libre de juicios, un refugio creado para que seas auténticamente vos. Vení con tu historia, tus ganas y tu cuerpo tal cual es hoy; nosotras nos encargamos de guiarte, con amor, paciencia y precisión, para sacar a la luz tu versión más radiante.
        </p>
      </section>

      {/* Section 4 */}
      <section className="py-20 px-6 max-w-4xl mx-auto border-t border-primary-main/20">
        <h2 className="font-marcellus text-3xl mb-8 text-center">✦ La corona de tu día: Una hora diseñada para vos</h2>
        <p className="font-sans text-center mb-8 leading-relaxed opacity-90">
          Tu tiempo es tu bien más preciado, y en Violett lo tratamos con el nivel de detalle que merecés. Cada vez que nos visitás, vivís una experiencia de 60 minutos milimétricamente pensada para tu bienestar:
        </p>
        <ul className="space-y-6 font-sans">
          <li>
            <strong>✦ 55 Minutos de Arte y Fluidez:</strong> Sobre el Reformer, despertamos la memoria de tus músculos. Restauramos tu elasticidad, aliviamos las tensiones diarias y moldeamos tu figura alargando la musculatura para lograr esa presencia esbelta, firme y libre de pesadez.
          </li>
          <li>
            <strong>✦ 5 Minutos de Pura Gloria:</strong> Un delicado regalo final. Cerramos tu práctica con nuestro característico masaje de descompresión. Es ese instante donde el mundo desaparece, porque toda princesa merece cerrar su día sintiéndose como la realeza: renovada y en perfecta paz.
          </li>
        </ul>
      </section>

      {/* Section 5 */}
      <section className="py-20 px-6 max-w-4xl mx-auto border-t border-primary-main/20">
        <h2 className="font-marcellus text-3xl mb-8 text-center">✦ El Estilo de Vida Violett</h2>
        <p className="font-sans text-center mb-8 leading-relaxed opacity-90">
          Ser parte de nuestro estudio es abrazar una filosofía de vida. Es la delicadeza de quien sabe que cuidar su cuerpo es el acto más puro de amor propio.
        </p>
        <ul className="space-y-4 font-sans">
          <li><strong>✦ La Silueta Soñada:</strong> Moldeamos tu figura con la sutileza del arte, alargando la musculatura para lograr esa presencia esbelta, firme y libre de pesadez.</li>
          <li><strong>✦ La Gracia en la Postura:</strong> Corregimos desde la raíz, devolviéndote la elegancia natural de una espalda erguida y un cuello relajado. Una postura que proyecta seguridad.</li>
          <li><strong>✦ El Privilegio de la Intimidad:</strong> Grupos sumamente reducidos. Una atención que se detiene en cada detalle de tu anatomía, asegurando que cada movimiento sea impecable y cuidado.</li>
          <li><strong>✦ La Paz Mental:</strong> El estrés se disuelve entre la luz natural y nuestro característico cierre: un delicado masaje final que corona tu esfuerzo, dejándote renovada y en perfecta armonía.</li>
        </ul>
      </section>

      {/* Section 6 */}
      <section className="py-20 px-6 max-w-4xl mx-auto text-center border-t border-primary-main/20">
        <h2 className="font-marcellus text-3xl mb-6">✦ 21 Años de Excelencia: El Método Débora Zárate</h2>
        <p className="font-sans mb-4 leading-relaxed opacity-90">
          Nuestra sofisticación nace de un conocimiento profundo. El Método Violett, creado por nuestra fundadora Débora Zárate tras más de dos décadas de impecable trayectoria, garantiza un estándar de calidad insuperable.
        </p>
        <p className="font-sans leading-relaxed opacity-90">
          No dejamos nada al azar. Cada instructora de nuestro equipo ha sido elegida y formada rigurosamente bajo esta misma filosofía: un equilibrio perfecto entre el conocimiento estricto de la anatomía, el cuidado y la empatía. Estás en manos de expertas que protegen tu salud integral mientras esculpen tu silueta.
        </p>
      </section>

      {/* Section 7 */}
      <section className="py-20 px-6 max-w-4xl mx-auto border-t border-primary-main/20">
        <h2 className="font-marcellus text-3xl mb-8 text-center">✦ Todo preparado para tu llegada</h2>
        <p className="font-sans text-center mb-8 leading-relaxed opacity-90">
          Sabemos que dar el primer paso puede generar dudas. En Violett, hacemos que cuidarte sea la parte más fácil de tu semana.
        </p>
        <ul className="space-y-6 font-sans mb-10">
          <li>
            <strong>✦ ¿Qué necesito llevar?</strong> Solo ropa deportiva con la que te sientas hermosa y cómoda, y tus medias antideslizantes (<em>grip socks</em>). Del aroma, la temperatura y la atmósfera perfecta nos encargamos nosotras.
          </li>
          <li>
            <strong>✦ ¿Es para mí si nunca entrené?</strong> Absolutamente. El Reformer nos permite adaptar cada movimiento a tu cuerpo y a tu ritmo, cuidando tus articulaciones desde el primer día.
          </li>
          <li>
            <strong>✦ ¿Cómo organizo mis tiempos?</strong> A través de nuestro sistema digital exclusivo, podés gestionar tu agenda y reservar tus momentos en Violett con total independencia y fluidez, sin intermediarios.
          </li>
        </ul>
        <div className="text-center">
          <Link 
            to="/login"
            className="inline-block bg-primary-main text-white font-sans font-medium px-8 py-4 rounded hover:opacity-90 transition-opacity"
          >
            ✦ Acceder a mi agenda personal
          </Link>
        </div>
      </section>

      {/* Section 8: Testimonials */}
      <section className="py-20 px-6 bg-primary-main/5 border-t border-primary-main/20">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-marcellus text-3xl mb-4 text-center">✦ Ecos de nuestra comunidad</h2>
          <p className="font-sans text-center mb-12 opacity-90">
            Mujeres que hicieron de la elegancia y el bienestar su estilo de vida diario.
          </p>
          <div className="grid md:grid-cols-2 gap-8">
            <blockquote className="p-6 bg-background rounded shadow-sm border border-primary-main/10">
              <p className="italic mb-4">"Buscaba un lugar que me inspirara a lograr la figura de mis sueños, y encontré un estilo de vida. Desde el aroma hasta el masaje final, todo te hace sentir radiante. Te aceptan, te cuidan y te elevan. Es la hora más linda de mi día."</p>
              <footer className="font-bold">— Martina C.</footer>
            </blockquote>
            <blockquote className="p-6 bg-background rounded shadow-sm border border-primary-main/10">
              <p className="italic mb-4">"Recuperé la firmeza y la flexibilidad, pero lo más hermoso es la energía vibrante con la que salgo para disfrutar mi día al máximo. Las profes son impecables y el método realmente cambia tu cuerpo."</p>
              <footer className="font-bold">— Silvia M.</footer>
            </blockquote>
          </div>
        </div>
      </section>

      {/* Section 9 */}
      <section className="py-20 px-6 max-w-4xl mx-auto text-center border-t border-primary-main/20">
        <h2 className="font-marcellus text-3xl mb-6">✦ Tu momento de brillar te espera</h2>
        <p className="font-sans mb-8 leading-relaxed opacity-90">
          Para mantener la excelencia, el silencio y el privilegio de la intimidad que nos caracteriza, <strong>los cupos en nuestro estudio son estrictamente limitados</strong>. Asegurá tu lugar en nuestra agenda y comenzá tu transformación.
        </p>
        <ul className="space-y-4 font-sans text-left inline-block mb-10 mx-auto max-w-2xl">
          <li><strong>✦ Tu Primera Invitación:</strong> Acercate a conocer la experiencia Violett y permitite sentir la belleza de un método diseñado a tu medida.</li>
          <li><strong>✦ Membresía Glow:</strong> Garantizá tu espacio en nuestra comunidad exclusiva, manteniendo la constancia que tu cuerpo merece.</li>
        </ul>
        <div>
          <Link 
            to="/login"
            className="inline-block bg-primary-main text-white font-sans font-medium px-8 py-4 rounded hover:opacity-90 transition-opacity"
          >
            ✦ Asegurar mi lugar hoy
          </Link>
        </div>
      </section>

      {/* Section 10: Memberships */}
      <section className="py-20 px-6 bg-primary-main/5 border-t border-primary-main/20">
        <div className="max-w-5xl mx-auto">
          <h2 className="font-marcellus text-3xl mb-6 text-center">✦ Tu Compromiso con la Elegancia: Nuestras Membresías</h2>
          <p className="font-sans text-center mb-2 leading-relaxed opacity-90">
            El amor propio se construye con constancia. Elegí la frecuencia que mejor se adapte a tu estilo de vida y comenzá a esculpir tu figura en nuestro refugio.
          </p>
          <p className="font-sans text-center mb-12 text-sm italic opacity-75">
            (Los valores se actualizan en tiempo real desde nuestra base de datos)
          </p>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-background p-8 rounded border border-primary-main/20 flex flex-col">
              <h3 className="font-marcellus text-xl mb-4 text-center">✦ Pausa Delicada<br/>(4 clases al mes)</h3>
              <p className="font-sans text-sm mb-6 flex-grow opacity-90">
                Ideal para quienes buscan complementar su rutina y regalarse un momento sagrado a la semana para alinear su postura y desconectar del mundo.
              </p>
              <ul className="text-sm font-sans space-y-2 mb-6">
                <li>• 1 clase semanal garantizada.</li>
                <li>• Acceso a nuestra plataforma de reservas.</li>
                <li><strong>Valor:</strong> $ [Precio dinámico]</li>
              </ul>
              <Link to="/login" className="block text-center border border-primary-main text-primary-main py-2 rounded hover:bg-primary-main hover:text-white transition-colors">
                ✦ Elegir este plan
              </Link>
            </div>

            <div className="bg-primary-main text-white p-8 rounded shadow-lg flex flex-col transform scale-105 z-10">
              <div className="text-xs font-bold tracking-widest text-center mb-2">✦ EL MÁS ELEGIDO ✦</div>
              <h3 className="font-marcellus text-xl mb-4 text-center">✦ Equilibrio Radiante<br/>(8 clases al mes)</h3>
              <p className="font-sans text-sm mb-6 flex-grow opacity-90">
                La constancia perfecta, elegida por la mayoría de nuestras alumnas. Dos encuentros semanales para moldear tu silueta, corregir tu espalda desde la raíz y notar cambios reales en tu energía y vitalidad.
              </p>
              <ul className="text-sm font-sans space-y-2 mb-6">
                <li>• 2 clases semanales para resultados visibles.</li>
                <li>• Acompañamiento personalizado.</li>
                <li><strong>Valor:</strong> $ [Precio dinámico]</li>
              </ul>
              <Link to="/login" className="block text-center bg-white text-primary-main py-2 rounded hover:bg-opacity-90 transition-colors font-bold">
                ✦ Quiero mi transformación
              </Link>
            </div>

            <div className="bg-background p-8 rounded border border-primary-main/20 flex flex-col">
              <h3 className="font-marcellus text-xl mb-4 text-center">✦ Plenitud Total<br/>(12 clases al mes)</h3>
              <p className="font-sans text-sm mb-6 flex-grow opacity-90">
                Para quienes hacen de su bienestar su prioridad absoluta. Tres momentos a la semana de inmersión total en el Método Violett, logrando la máxima elasticidad, firmeza y paz mental.
              </p>
              <ul className="text-sm font-sans space-y-2 mb-6">
                <li>• 3 clases semanales de cuidado intensivo.</li>
                <li>• Máxima prioridad en nuestra agenda.</li>
                <li><strong>Valor:</strong> $ [Precio dinámico]</li>
              </ul>
              <Link to="/login" className="block text-center border border-primary-main text-primary-main py-2 rounded hover:bg-primary-main hover:text-white transition-colors">
                ✦ Elegir la inmersión total
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Section 11 */}
      <section className="py-20 px-6 max-w-4xl mx-auto text-center border-t border-primary-main/20">
        <h2 className="font-marcellus text-3xl mb-6">✦ Un entorno diseñado para tu tranquilidad</h2>
        <p className="font-sans mb-10 leading-relaxed opacity-90">
          Porque sabemos que apreciás el orden y la exclusividad, creamos una experiencia digital a la altura de nuestro estudio. A través de nuestro sistema privado, podés coordinar tus momentos en Violett con total delicadeza, gestionando tu tiempo con la misma fluidez y armonía que experimentás en nuestras camas.
        </p>
        <Link 
          to="/login"
          className="inline-block bg-primary-main text-white font-sans font-medium px-8 py-4 rounded hover:opacity-90 transition-opacity"
        >
          ✦ Acceder a mi agenda personal
        </Link>
      </section>

      {/* Footer */}
      <footer className="py-10 px-6 text-center border-t border-primary-main/20 font-sans opacity-80">
        <p className="font-bold mb-2 text-lg">Violett ✦ Pilates</p>
        <p className="mb-4">📍 Gral. Guido 1573, Ramos Mejía.</p>
        <p className="text-sm">© 2026 Violett.</p>
      </footer>
    </div>
  );
}
