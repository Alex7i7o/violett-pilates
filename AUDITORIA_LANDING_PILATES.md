# 🔍 Auditoría Integral de Diseño, Copywriting y Conversión (CRO)
**Sitio auditado:** `violett.com.ar/pilates`  
**Archivos analizados:**  
- [LandingView.tsx](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/src/pages/public/LandingView.tsx) *(Landing principal servida en `/pilates/`)*  
- [PilatesLanding.tsx](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/landings/src/pages/PilatesLanding.tsx) *(Landing secundaria en el contenedor `/pilates`)*  
- [index.css](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/src/index.css) *(Sistema tipográfico y tokens visuales)*  

**Frameworks aplicados en esta auditoría:**  
- **High-Converting Landings & CRO** *(Ecuación de Valor de Alex Hormozi, 5 Niveles de Consciencia de Eugene Schwartz y las 7 Fugas Fatales de Conversión)*.  
- **Emotional Brand Marketing** *(Comunicación estilo Apple: Show Don't Tell, Pirámide del Deseo y Mecanismo Único)*.  
- **Design Engineering (`emil-design-eng`)** *(Pulido de interfaz, micro-interacciones, jerarquía óptica y rendimiento en móviles)*.

---

## 1. Veredicto Ejecutivo: ¿La Landing Vende o No Vende?

> **Puntaje actual de Conversión (CRO): 5.5 / 10**  
> **Puntaje de Estética y Atmósfera de Marca: 7.5 / 10**

### Diagnóstico Directo:
Hoy la página funciona como un **folleto literario institucional ("Brand Brochure")**, pero **NO como una máquina de ventas para tráfico frío o tibio**.

- **A quién SÍ le vende hoy:** A la mujer **Hiper-Consciente (Nivel 5)** que ya conoce a Débora, vive a tres cuadras o viene recomendada por una amiga, y solo entra a la web para ver cuánto sale el mes de 8 clases o tocar el botón de WhatsApp.
- **A quién PIERDE hoy (60% al 75% de fuga estimada):** A la mujer que llega desde Instagram, Google Maps o buscando *"Pilates Reformer en Ramos Mejía"*. Esa visitante escanea la página en **5 segundos desde el celular**: no ve ni una sola foto real del estudio, no ve las camas Reformer, no ve cuántos cupos hay por clase en el primer pantallazo, y se topa con 11 bloques seguidos de texto poético muy parecido entre sí.

---

## 2. Lo Que Está Mal (Las 6 Fugas Críticas de Ventas y Diseño)

### 🔴 1. Cero Evidencia Visual Real (No hay fotos del estudio, de las camas ni de Débora)
En las 576 líneas de [LandingView.tsx](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/src/pages/public/LandingView.tsx), **no existe ni una sola fotografía o video del estudio**. Los únicos gráficos son el isotipo y el logotipo.
- **Por qué mata la conversión:** En el rubro de bienestar, estética y Pilates Boutique, **la clienta compra con los ojos**. Si el texto promete *"luz natural, madera noble, silencio e intimidad"*, pero la pantalla solo muestra fondos blancos/lilas vacíos, el cerebro del prospecto siente incertidumbre (*"¿Cómo será el lugar realmente? ¿Será una habitación chica o un estudio de verdad?"*).
- **Impacto en la Ecuación de Valor:** Sin fotos reales del salón, de los Reformers y del rostro de Débora Zárate, la **Certeza Percibida** cae a la mitad.

### 🔴 2. El "Above the Fold" (Primeros 5 Segundos) desperdicia el Titular Principal
Cuando una persona abre la web en su celular, esto es lo que ve:
1. Un logo gigante (`w-24` / `w-36`).
2. Un `<h1>` que dice simplemente **"Violett Pilates"** (repitiendo el nombre que ya está en el logo del header).
3. Un `<h2>` poético: *"✦ El arte de esculpir la silueta de tus sueños y habitar tu cuerpo con elegancia"*.
4. Un párrafo literario de **74 palabras** (*"Lejos del ruido del mundo, existe un espacio donde el tiempo parece detenerse..."*).
- **Qué falta en los primeros 5 segundos:** La visitante tiene que adivinar los 3 mayores diferenciales comerciales de Violett, que recién aparecen enterrados a mitad de página:
  - **Máximo 3 camillas Reformer por turno** (atención casi privada, no un gimnasio masivo de 12 camas).
  - **Ritual 55 + 5** (55 min de Reformer + 5 min de masaje de descompresión al finalizar).
  - **Dirección de Débora Zárate** (21 años de trayectoria formando instructoras).
- *(Nota: En la landing de Violett Estética esto sí se hizo bien con las 3 tarjetas de credibilidad debajo de los botones del Hero; en Pilates falta por completo).*

### 🔴 3. Textos Duplicados Literalmente (Copia y Pega entre Secciones 2, 4 y 5)
La página tiene **11 secciones de texto**, lo cual genera fatiga de scroll en móvil, agravado porque **se repiten exactamente las mismas frases palabra por palabra**:
- **En Sección 2 (Línea 200):** *"despertamos la memoria de tus músculos. No solo restauramos esa elasticidad..."*
- **En Sección 4 (Línea 230):** *"Sobre el Reformer, despertamos la memoria de tus músculos. Restauramos tu elasticidad, aliviamos las tensiones diarias y moldeamos tu figura alargando la musculatura para lograr esa presencia esbelta, firme y libre de pesadez."*
- **En Sección 5 (Línea 254):** *"Moldeamos tu figura con la sutileza del arte, alargando la musculatura para lograr esa presencia esbelta, firme y libre de pesadez."*
- **Efecto en el lector:** Cuando una clienta lee tres veces la misma oración exacta en menos de 20 segundos de scroll, percibe relleno (*filler text*) y deja de leer el resto de la página.

### 🔴 4. Choque Visual de Alineación: Títulos a la Izquierda + Párrafos Centrados
En todas las secciones de [LandingView.tsx](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/src/pages/public/LandingView.tsx) (líneas 160, 193, 208, 219, 246, 270, 285, 316, 367, 409, 502):
- Todos los títulos `<h2>` tienen la clase `text-left w-full`.
- Todos los párrafos `<p>` inmediatamente debajo tienen la clase `text-center`.
- **Por qué se ve mal:** En diseño editorial, combinar un encabezado tirado al margen izquierdo con un párrafo centrado debajo rompe el eje óptico vertical (la columna vertebral de lectura). El ojo tiene que zigzaguear de izquierda a centro en cada bloque.

### 🔴 5. Falta la "Clase Inaugural / Clase de Prueba" en la Sección de Precios
- En la Sección 9 el texto invita a **"Tu Primera Invitación"** (ir a probar y conocer el método).
- En la base de datos y en el bot de WhatsApp existe la **Clase Única ($20.000)**.
- Pero cuando la usuaria llega a la grilla de `#membresias` (Sección 10), solo ve planes mensuales de **4, 8 y 12 clases**.
- **Fuga de conversión:** La mujer que nunca hizo Pilates Reformer o que quiere conocer las camas antes de pagar el mes entero no encuentra un botón para **"Agendar mi Clase Inaugural / Clase de Prueba"**.

### 🔴 6. Peligro Técnico: Existen DOS Landings de Pilates distintas en el repositorio
- En `https://violett.com.ar/pilates/` (con barra) Nginx sirve [LandingView.tsx](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/src/pages/public/LandingView.tsx) (la versión completa).
- Pero en el proyecto `landings` ([App.tsx](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/landings/src/App.tsx#L17)) existe `<Route path="/pilates" element={<PilatesLanding />} />` que renderiza [PilatesLanding.tsx](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/landings/src/pages/PilatesLanding.tsx): una landing vieja que no tiene precios, no tiene WhatsApp, habla de "Violetita" y tiene botones rotos que apuntan a `/pilates/app/`. Si alguien navega desde la raíz de `violett.com.ar` hacia `/pilates` sin recargar Nginx, cae en la landing vieja rota.

---

## 3. Lo Que Sí Funciona Muy Bien (No Tocar)

1. **El Mecanismo Único "55 + 5" (Sección 4):** Explicar que la clase se divide en *55 minutos de trabajo en Reformer + 5 minutos de masaje de descompresión final* es oro puro en copywriting. Es concreto, memorable y justifica el posicionamiento boutique.
2. **Precios Transparentes en Tiempo Real desde la API:** Mostrar los valores reales de 4, 8 y 12 clases filtra curiosos, genera confianza inmediata y posiciona al estudio con honestidad comercial.
3. **Psicología de Anclaje en la Tarjeta Central (Plan 8 Clases):** El destacado visual en violeta profundo (`bg-primary-main`), el ligero escalado (`lg:scale-105`), la etiqueta *"✦ EL MÁS ELEGIDO ✦"* y el CTA diferencial (*"Quiero mi transformación"*) cumplen a la perfección la ley de dirigir la mirada al plan más rentable y efectivo.
4. **Enlaces de WhatsApp con Contexto Pre-Cargado:** Que cada botón envíe un mensaje distinto (*"Hola Deby! ✦ Quiero el plan Equilibrio Radiante (8 clases)..."*) reduce la fricción de inicio de conversación a cero.
5. **Reseñas Dinámicas Conectadas al Sistema (`/resenas/`):** Mostrar testimonios reales cargados por las alumnas desde la plataforma le da frescura y prueba social genuina.

---

## 4. Tabla Técnica de Correcciones (Before / After — Design Engineering)

| Before | After | Why |
| --- | --- | --- |
| **11 secciones largas** con beneficios repetidos en Secciones 2, 4 y 5 | **6 secciones de alto impacto** sin repetir una sola frase | Elimina la fatiga de lectura en móvil y mantiene el ritmo persuasivo hasta el precio |
| `<h1>Violett Pilates</h1>` + `<h2>` alineado a la izquierda en un Hero centrado | Badge superior + `<h1>` de **propuesta de valor clara** centrado + subtítulo conciso | El H1 debe vender la transformación y el diferencial en menos de 3 segundos |
| Sin indicadores rápidos en el Hero | **3 Badges de Credibilidad** bajo los botones: `Máx. 3 Camillas por Turno`, `Ritual 55' + 5' Masaje`, `21 Años de Trayectoria` | Ancla hechos concretos (Capa Racional) debajo de la promesa emocional |
| `h2` con `text-left w-full` y `p` con `text-center` en todas las secciones | `h2` y `p` alineados sobre el **mismo eje óptico** (`text-center` en cabeceras de sección) | Corrige el salto visual zigzagueante entre título y párrafo |
| Cero imágenes del estudio o de Débora | Galería/Cards visuales del estudio, los Reformers y foto de autoridad de Débora Zárate | La prueba visual real multiplica la Certeza Percibida en servicios presenciales |
| Solo 3 planes mensuales (4, 8 y 12 clases) en `#membresias` | Los 3 planes mensuales + **Banner inferior de "Sesión Inaugural / Clase Individual"** | Captura a las prospectos indecisas que quieren probar una clase antes de pagar el mes |
| `filter: 'blur(4px)'` en cada `fadeUp` y `useTransform(scrollY, [0, 800], [1, 0])` en el Hero | Animar solo `opacity` y `transform: translateY()` sin desvanecer los botones del Hero al scrollear | Evita caída de FPS en celulares y garantiza que los botones del Hero siempre sean legibles |
| Ruta duplicada `/pilates` en `landings/src/App.tsx` con links a `/pilates/app/` | Redirigir `/pilates` directamente a `/pilates/` (o unificar con la landing real) | Evita que visitantes caigan en la versión vieja sin precios ni WhatsApp |

---

## 5. Nueva Arquitectura y Copywriting Recomendado (Listo para Implementar)

Para que la landing pase de **5.5/10 a 9.5/10 en conversión**, debemos compactar las 11 secciones actuales en **6 bloques quirúrgicos**:

### Bloque 1: Hero (Above the Fold — Claridad + Emoción + Prueba Rápida)
- **Badge Superior:** `ESTUDIO BOUTIQUE DE PILATES REFORMER • RAMOS MEJÍA`
- **Titular (H1):** `Esculpí tu silueta, aliviá tu espalda y recuperá tu paz mental en grupos exclusivos de solo 3 camillas.`
- **Subtitular (H2):** `Un refugio íntimo creado por Débora Zárate (21 años de trayectoria), donde combinamos 55 minutos de Pilates Reformer personalizado con 5 minutos de masaje de descompresión final.`
- **CTAs:**
  - Primario: `✦ Ver Planes y Precios` (`#membresias`)
  - Secundario: `🌸 Consultar Cupos con Débora` (WhatsApp directo)
- **3 Cápsulas de Certeza (debajo de los botones):**
  1. **Máximo 3 Camillas por Turno:** Atención casi privada, sin salones masivos ni ruidosos.
  2. **Ritual 55' + 5' de Gloria:** Cerramos cada sesión con un masaje descontracturante asistido.
  3. **Agenda Digital Sin Fricción:** Reservá o reprogramá tus turnos desde el celular en segundos.

### Bloque 2: Para Quién Es y Qué Resuelve (Dolor vs. Transformación)
Unificar las actuales Secciones 2, 3 y 5 en una sola grilla limpia de 4 pilares (sin repetir textos):
1. **Silueta Firme y Estilizada:** Tonificá y alargá tu musculatura sin impacto articular ni agotamiento extremo.
2. **Espalda Libre de Dolores:** Corregí tu postura desde la raíz y liberá la tensión cervical y lumbar acumulada en la semana.
3. **Sin Experiencia Previa:** Adaptamos la resistencia de los resortes del Reformer a tu cuerpo y a tu ritmo desde el primer día.
4. **Intimidad Absoluta:** Solo 3 mujeres por clase en un ambiente climatizado, perfumado y libre de miradas o juicios.

### Bloque 3: La Experiencia Violett (El Mecanismo Único "55 + 5")
Mantener la actual Sección 4 (que es excelente), puliendo el texto para que no repita frases del bloque anterior.

### Bloque 4: Autoridad Fundacional (21 Años — El Método Débora Zárate)
Destacar la trayectoria de Débora Zárate y cómo cada profesora del equipo es formada personalmente por ella bajo un criterio anatómico estricto (sumando un contenedor para su foto o firma personal).

### Bloque 5: Membresías en Tiempo Real + Opción de Clase Inaugural
Mantener las 3 tarjetas conectadas a la API (`Pausa Delicada - 4 clases`, `Equilibrio Radiante - 8 clases`, `Plenitud Total - 12 clases`) y agregar debajo una tarjeta horizontal destacada:
> **¿Querés vivir la experiencia antes de elegir tu plan mensual?**  
> Agendá tu **Clase Inaugural en Camilla Reformer** (incluye evaluación postural + ritual de 5 min de masaje final) → `[Reservar Mi Clase Inaugural por WhatsApp]`

### Bloque 6: Prueba Social Real (Reseñas de Alumnas) + Preguntas Frecuentes (FAQ)
Las reseñas conectadas a la API seguidas de las 3 preguntas clave (*¿Qué necesito llevar?*, *¿Puedo empezar de cero?*, *¿Cómo funcionan los turnos y recuperos?*) y el cierre directo a WhatsApp.
