# Auditoría UX/UI: De Web Adaptada a "Native-First" (Estilo Apple / Premium)

Actualmente, el sistema está construido con un enfoque **"Responsive Web"** (se adapta al ancho de pantalla), pero no **"Mobile-Native"** (pensado para el pulgar y los patrones de iOS/Android). Para lograr que se sienta como una aplicación costosa de $50,000 USD, debemos cambiar la estructura fundamental de la interfaz.

A continuación, los problemas detectados y el plan de acción para solucionarlos.

---

## 1. El Problema de la Navegación (Bottom Tabs vs Top Header)
**El problema:** Actualmente tenemos un "Header" (encabezado) en la parte superior con un botón de "Cerrar Sesión". Este es un patrón 100% de escritorio. Obliga al usuario a estirar el pulgar hasta arriba.
**La solución "Native":**
- Eliminar los botones de acción del encabezado.
- Crear una **Bottom Tab Navigation** (Barra de navegación inferior) translúcida (Glassmorphism) con 3 íconos: `Inicio`, `Mis Reservas`, `Perfil`.
- El botón de "Cerrar Sesión" y los datos del plan se mudan a la pestaña `Perfil`.
- El encabezado superior queda limpio, solo con un título grande (estilo "Large Title" de iOS) que se achica al hacer scroll.

## 2. El Problema del "App Feel" (PWA & Browser Chrome)
**El problema:** Al entrar desde Safari o Chrome, se ve la barra de direcciones (URL), la barra de herramientas del navegador, y la pantalla "rebota" de forma extraña si scrolleás más allá del límite (el temido *rubber-banding* web).
**La solución "Native":**
- **Meta Tags de PWA:** Agregar `apple-mobile-web-app-capable` y `status-bar-style: black-translucent` en el `index.html`. Esto permite a las alumnas tocar "Agregar a la pantalla de inicio" y que la app se abra a pantalla completa (sin barra de URL).
- **Overscroll Behavior:** Desactivar el rebote del `<body>` (`overscroll-behavior-y: none`) y habilitarlo solo dentro de las listas (`-webkit-overflow-scrolling: touch`), para que el scroll se sienta con "momentum" natural de iOS, pero sin que se mueva toda la app.

## 3. Gestos, Toques y Micro-interacciones
**El problema:** Las webs usan el estado `:hover` (cuando pasas el mouse). En iOS, si tocás un botón con `:hover`, a veces el color se queda "pegado" hasta que tocás otra cosa. Además, faltan respuestas físicas (haptics).
**La solución "Native":**
- **Eliminar Hovers en Mobile:** Configurar Tailwind para que los efectos de "hover" solo apliquen si el dispositivo soporta mouse (`@media (hover: hover)`).
- **Estados Active:** Aumentar el uso del estado `active:scale-95` y `active:opacity-70`. Cuando la alumna aprieta un botón, debe reaccionar instantáneamente bajo su dedo antes de soltarlo.
- **Haptics (Vibración):** Al confirmar o cancelar una reserva, disparar un micro-pulso de vibración (`navigator.vibrate(50)`).
- **Pull-to-refresh:** En lugar de tener que recargar la página, permitir que la usuaria arrastre la pantalla hacia abajo para actualizar los turnos disponibles.

## 4. Layout de Listas vs Tarjetas (Cards)
**El problema:** En móvil, envolver todo en rectángulos flotantes (Cards) con sombras pesadas reduce el espacio útil y parece un "Dashboard web apretado".
**La solución "Native":**
- Las listas (ej. clases disponibles) en móvil deben ir de borde a borde (Edge-to-Edge) separadas por finas líneas (`border-b`), maximizando el espacio de lectura.
- Dejar las "Cards" flotantes solo para destacar información crítica (como el Plan Activo).
- Asegurar que todo elemento tocable tenga al menos **44x44 píxeles** de tamaño real (la regla de oro de accesibilidad de Apple).

## 5. Animaciones de Transición de Pantalla
**El problema:** Actualmente, al cambiar de página, usamos un "Fade Up" (Aparición hacia arriba). Es lindo, pero no es nativo.
**La solución "Native":**
- Las nuevas pantallas deben entrar **deslizándose desde la derecha** (Slide In), simulando el "Stack Navigator" nativo de iOS/Android. Y al volver atrás, deslizarse hacia la izquierda.

---

## 🚀 Plan de Ejecución Propuesto (Próximos Pasos)

Si estás de acuerdo con esta visión, te propongo empezar por el **Paso 1 y 2**, que van a cambiar el 80% de la percepción de la app:

1. **Construir la BottomNavigation:** Borramos el header pesado, creamos la barra inferior con íconos, y separamos la vista principal en 3 pestañas limpias.
2. **Convertirla en PWA:** Configuramos el `index.html` para que se pueda instalar en el celular como una App nativa (sin barra de direcciones).
3. **Optimizar Táctil:** Cambiamos los botones de tarjetas a listas Edge-to-Edge y pulimos los efectos al tocar (`active:`).
