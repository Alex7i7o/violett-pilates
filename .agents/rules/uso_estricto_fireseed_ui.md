# Regla de Oro: Uso Obligatorio de fireseed-ui como Motor Gráfico

El ecosistema de FireSeed (Violett Pilates, Estética, Portfolio de Alex Agüero y futuros proyectos B2B) utiliza **`fireseed-ui`** como su sistema de diseño atómico y motor visual oficial.

Para garantizar consistencia de marca de alto lujo, rendimiento nativo a 60 FPS y cero duplicación de estilos, **TODOS LOS AGENTES DE IA DEBEN CUMPLIR ESTAS DIRECTIVAS ESTRICTAS:**

---

### 1. Prohibido Reinventar la Rueda en UI
* **Terminantemente Prohibido:** No maquetes desde cero componentes de interfaz (botones, badges, modales, tarjetas, switches, inputs, tooltips, drawers, spinners) dentro de las aplicaciones clientes o landings usando HTML/CSS crudo.
* **Obligatorio:** Consume siempre los componentes oficiales exportados por el paquete:
  ```tsx
  import { Button, Badge, Modal, Card, InputField, Switch, Tooltip } from 'fireseed-ui';
  ```

---

### 2. Flujo de Extensión (Si falta algo, se crea en la librería)
* Si un proyecto requiere un nuevo componente visual o una variante que aún no existe en `fireseed-ui`:
  1. Se desarrolla primero dentro del paquete `fireseed-ui/src/components/`.
  2. Debe cumplir con los estándares de la librería: tokens semánticos de Tailwind v4, microinteracciones hápticas (`navigator.vibrate`), accesibilidad WAI-ARIA (Focus Trap / roles ARIA) y animaciones de física física (`spring`).
  3. Se compila con `npm run build:lib` y se consume en las aplicaciones cliente.
  *Nunca dejes componentes sueltos o duplicados en las carpetas locales de una app.*

---

### 3. Respeto Irrestricto de Tokens Semánticos
* Todos los componentes deben respetar la paleta semántica del ecosistema:
  * Fondo Imperial: `#14071E` / `#0D041A`
  * Superficies Elevadas: `#241142`
  * Acentos de Oro: `#DAAF6C` / `#FBBF24`
  * Tipografías y textos: `#FFF6DF` (Cream Silk)
* No uses colores hexadecimales arbitrarios fuera de los tokens semánticos oficiales.

---

### 4. Animaciones y Rendimiento Físico
* Todas las animaciones interactivas (hover, tap, modales) deben utilizar física de resortes (`spring` con `stiffness: 400, damping: 25`) sin retrasos artificiales (`delay: 0` en hover) para garantizar respuesta táctil instantánea.
* Nunca mezcles `transition-all` de CSS con transformaciones dinámicas de Framer Motion.
