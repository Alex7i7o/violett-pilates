---
description: Regla crítica de aislamiento entre clientes (Pilates vs Estética) para evitar regresiones.
trigger: always_on
---

# Regla de Oro: Aislamiento de Marcas (Pilates vs Estética)

El proyecto FireSeed utiliza una arquitectura **Multi-Tenant en tiempo de compilación (Compile-Time Toggling)** basada en client-config.json. Ambos clientes (Pilates y Estética) comparten el mismo repositorio de código, pero compilan de forma diferente según los plugins activos.

Para garantizar que el trabajo en una marca no rompa la otra, **TODOS LOS AGENTES DE IA DEBEN CUMPLIR ESTAS DIRECTIVAS:**

### 1. El Núcleo (Core) es Intocable por Defecto
Cualquier modificación en engine/backend/core/ o engine/frontend/src/core/ afectará a **AMBAS** aplicaciones simultáneamente.
* **Prohibido:** No agregues lógica de negocio específica de "Estética" o "Pilates" en el Core.
* **Permitido:** Solo se modifica el Core para arreglos de infraestructura general, seguridad, o utilidades que benefician a todo el ecosistema de forma agnóstica.

### 2. Plugins Compartidos (Cuidado Extremo)
Plugins como uth, pagos y comunicaciones se usan en ambas apps.
* Si haces un cambio visual o lógico en ellos, **siempre** debes considerar: *"¿Cómo se verá o afectará esto a Pilates?"*. Utiliza variables booleanas como isEstetica (leyendo el client-config.json) para renderizar condicionalmente si es necesario un cambio visual específico en un plugin compartido.

### 3. Desarrollo Aislado (La Vía Correcta)
Cuando vayas a crear el "motor" o lógicas específicas para Estética (ej. máquinas, gabinetes, tiempos de tratamiento), **debes hacerlo estrictamente dentro de plugins dedicados**, como por ejemplo:
* engine/plugins/estetica_agenda/
* engine/plugins/estetica_servicios/
Estos plugins estarán desactivados en el client-config.json de Pilates, garantizando matemáticamente que si rompes el plugin de Estética, el negocio de Pilates seguirá funcionando al 100%.

### 4. Bases de Datos Separadas
Recuerda que en el docker-compose.yml, las bases de datos de Pilates y Estética son contenedores Postgres independientes. No hay riesgo de cruce de datos, pero los modelos de BD en el código sí son compartidos si están en el Core o en plugins compartidos.
