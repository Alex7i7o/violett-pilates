# Filosofía de Diseño: Estándar "App Nativa" (Native-First)

Este documento detalla los principios de diseño e ingeniería de interfaces utilizados para transformar plataformas web tradicionales en experiencias que se sienten idénticas a una **Aplicación Nativa Premium** (iOS y Android), basándonos en las *Human Interface Guidelines (HIG)* de Apple y *Material Design*.

---

## 1. Mobile-First Verdadero (No solo "Responsive")
No encogemos interfaces de computadora para que "entren" en la pantalla de un celular (eso es diseño adaptativo clásico). En su lugar, construimos la experiencia táctil móvil de cero pensando en la ergonomía de los pulgares, y luego expandimos esa experiencia (agregando columnas o barras laterales) cuando detectamos pantallas de escritorio.

## 2. Chau Menú Hamburguesa superior ➡️ Bottom Tab Bar
El botón de "menú hamburguesa" en la esquina superior izquierda es un remanente del diseño web de la década pasada. Es inalcanzable para el pulgar en teléfonos modernos.
- **En Móvil:** Utilizamos una **Bottom Tab Bar** (Barra de Pestañas Inferior) fija. Contiene máximo 4 o 5 destinos principales, claramente identificables con iconos (Lucide Icons).
- **En Desktop:** Esta barra desaparece y se transforma en una Sidebar (Barra Lateral) expansiva a la izquierda.

## 3. Menús Secundarios como "Bottom Sheets"
Cuando hay más de 4 destinos (ej: Panel de Administrador), el 4to ícono de la Bottom Tab Bar siempre es **"Más" (Menú)**. 
En lugar de abrir un menú lateral a pantalla completa, este botón desliza un **Bottom Sheet (Modal inferior)** suave desde abajo. Esto mantiene el contexto de la aplicación de fondo, es ergonómico y se siente 100% nativo.

## 4. Desacoplamiento de Vistas en Móvil
Si una pantalla en Desktop (PC) contiene mucha información en simultáneo (ej. Tablero panorámico con Agenda a la izquierda y Bolsa de Trabajo a la derecha), **nunca apilamos todo en un scroll infinito vertical para celular**.
- **Solución:** Rompemos la vista de PC en múltiples vistas enfocadas para el celular, asignando cada columna o bloque a una pestaña diferente en la Bottom Tab Bar o en Segmented Controls (botones estilo Apple). El usuario hace scroll horizontal o cambia de pestaña, pero nunca se pierde en un pozo de scroll infinito.

## 5. Carga de Datos: Skeletons > Spinners
Evitamos los clásicos "círculos girando" (Spinners) para cargar pantallas completas.
- **Solución:** Utilizamos **Skeleton Loaders** (siluetas grises con `animate-pulse` usando Tailwind CSS) que tienen la forma exacta del componente final (ej: forma de tarjeta). Esto evita el CLS (*Cumulative Layout Shift*), es decir, que la pantalla "salte" violentamente cuando los datos finalmente llegan de la base de datos.

## 6. Feedback Visual y Fluidez (Motion)
Una web nativa nunca es rígida. Cada interacción tiene feedback.
- Utilizamos **Framer Motion** (`<AnimatePresence mode="wait">`) para que los cambios de pestaña cruzados (fade-in / fade-out) y los modales reaccionen fluidamente sin parpadeos de carga (blinking).
- Todos los botones tocables tienen un estado `:active` (`active:scale-95` en Tailwind) para imitar la contracción física de la pantalla al presionar (Push feedback).

## 7. Safe-Area y Detalles de Sistema Operativo
Las apps web suelen chocar con las interfaces del propio teléfono (El "Notch", la barra de estado superior, o la barra gestual de inicio en la parte inferior de los iPhones).
- Inyectamos CSS específico: `padding-bottom: env(safe-area-inset-bottom)` (o clases personalizadas como `pb-safe`) para obligar a nuestra Tab Bar a flotar por encima del "Home Indicator" del iPhone.

## 8. PWA, Instalación y Erradicación del "Browser UI"
Para que la ilusión sea perfecta, la URL y la barra de navegación del navegador (Chrome/Safari) deben desaparecer.
- Forzamos la instalación de la PWA (Progressive Web App) con modales personalizados (ver `InstallAppModal.tsx`).
- Incluimos las meta etiquetas modernas (y legacy) de iOS: `<meta name="mobile-web-app-capable" content="yes">` y `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`. Esto permite que al abrirse desde la pantalla de inicio del celular, la aplicación corra a pantalla completa nativa sin marcos del navegador.
