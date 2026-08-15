# 🚀 Guía de Arquitectura, Estándares de Código y Reglas Globales — FireSeed

Este documento establece las directrices, arquitecturas, patrones de diseño y estándares técnicos obligatorios para el desarrollo de aplicaciones en **FireSeed**. Todas las herramientas de asistencia por IA y desarrolladores deben seguir estas reglas estrictamente.

---

## 1. Identidad de Marca y Firma (FireSeed)

* **Firma en Código:** Todo archivo de configuración principal, script de entrada o módulo raíz debe incluir el encabezado de comentario:
  `/* Developed by FireSeed - Fueling Innovation */` (o su equivalente en Python `# Developed by FireSeed - Fueling Innovation`).
* **Firma en UI:** El pie de página (`Footer`) de la interfaz de usuario debe incluir sutilmente la leyenda *"Powered by FireSeed"*.
* **Firma en Consola:** Incluir un script inicial que imprima en la consola del navegador un mensaje estilizado de bienvenida de FireSeed al cargar la aplicación.

---

## 2. Stack Tecnológico Estándar

* **Frontend:** React, TypeScript, Tailwind CSS, Framer Motion.
* **Backend:** Django, Django REST Framework / Ninja.
* **Base de Datos:** PostgreSQL (Preferido) / MySQL.
* **Lenguajes:** HTML5, CSS3, JavaScript (ES6+), TypeScript, Python 3.10+.
* **Tareas Asíncronas & Cron Jobs:** Celery + Redis (o Django-Q).

---

## 3. Arquitectura Modular Frontend ("Piezas de Lego")

* **Diseño Atómico/Componentizado:** La interfaz debe construirse a partir de componentes de React aislados, reutilizables y con responsabilidad única (ej. `Button`, `Modal`, `Card`, `InputField`).
* **TypeScript Estricto:** Define interfaces y tipos (`types/` e `interfaces/`) explícitos para todas las props, estados y respuestas de la API. **Queda estrictamente prohibido el uso de `any`**.
* **Personalización Dinámica (Design Tokens):**
  * Todos los colores, tipografías, radios de borde y sombras deben consumirse exclusivamente desde `tailwind.config.js` o variables CSS nativas.
  * Cambiar una variable en la configuración global debe actualizar la estética de toda la aplicación de forma inmediata.

---

## 4. Estética de Lujo, UX y Animaciones (Framer Motion)

* **Diseño Minimalista y Elegante:** Uso de paletas de colores sobrias, excelente jerarquía visual, uso generoso del espacio en blanco y bordes suaves.
* **Microinteracciones Sutiles:** Utilizar `framer-motion` para animaciones fluidas (hover de botones, transiciones de página, entrada de modales y estados de carga).
* **Regla de Rendimiento de UX:** Las animaciones deben tener una duración de entre **200ms y 400ms**. Nunca deben entorpecer la navegación del usuario ni saturar la interfaz.

---

## 5. Arquitectura de Software y Principios SOLID

### A. Principios SOLID & Clean Code
* **Single Responsibility Principle (SRP):**
  * **En Frontend:** Separa la lógica de estado y peticiones HTTP (mediante **Custom Hooks**) de la capa visual de renderizado (Componentes de Presentación).
  * **En Backend:** Mantén las vistas (`views.py`) delgadas. Toda la lógica de negocio compleja debe habitar en módulos de servicio (`services.py`).
* **KISS & DRY:** Prioriza la legibilidad y la reutilización sobre la sobreingeniería.

### B. Estructura de Capas en Backend (Django)
* `models.py`: Esquema de base de datos, relaciones y validaciones básicas.
* `services.py`: Casos de uso y reglas de negocio (ej. lógica de 25hs, cálculo de cupos, asignación de recurrencias).
* `views.py` / `api.py`: Recepción de peticiones HTTP, invocación de servicios y retorno de respuestas JSON.
* `tasks.py`: Tareas asíncronas en segundo plano (Celery / Cron Jobs).

### C. Gestión de Estado y Datos en Frontend
* **Custom Hooks:** Encapsula las llamadas a la API (fetch/axios) y el estado de la aplicación en hooks reutilizables (ej. `useBookings`, `useAuth`, `useSlots`).
* **Manejo de Estados:** Maneja explícitamente los estados de carga (`isLoading`), éxito (`isSuccess`) y error (`error`).

### D. Concurrencia y Transacciones
* **Transacciones Atómicas:** Toda operación que altere múltiples registros (ej. crear reserva + descontar crédito del plan) debe envolverse en una transacción atómica (`@transaction.atomic`).
* **Prevenir Race Conditions:** Usar bloqueos o consultas seguras al actualizar cupos en tiempo real.

---

## 6. Estándares y Diseño de Base de Datos

### A. Integridad de Datos y Restricciones
* **Validaciones a Nivel de DB:** Aplica restricciones explícitas (`CheckConstraint`, `UniqueConstraint`) para garantizar coherencia (ej. `cupos_disponibles >= 0`).
* **Borrado Lógico (Soft Delete):** No eliminar registros críticos (usuarios, planes, transacciones, historial) con `DELETE`. Usar `is_active = False` o `deleted_at` para preservar la trazabilidad.

### B. Optimización e Índices
* **Indexación de Consultas Frecuentes:** Agregar índices (`db_index=True`) en campos de alta lectura como fechas/horas de clases, estados de reserva y claves foráneas.
* **Consultas Eficientes:** En Django ORM, utilizar `select_related()` y `prefetch_related()` para evitar el problema de consultas $N+1$.

### C. Manejo de Fechas y Zonas Horarias
* **Formato UTC:** Almacenar todas las fechas y horas en formato **UTC con Zone-Awareness** (`DateTime` con `timezone.now()`). La conversión a la hora local del usuario se realiza en el frontend.
* **UUIDs:** Utilizar `UUID` para identificadores públicos en URLs o tokens por razones de seguridad.

---

## 7. SEO, Accesibilidad y Documentación

* **HTML Semántico:** Utilizar etiquetas semánticas de HTML5 (`<header>`, `<main>`, `<nav>`, `<section>`, `<footer>`).
* **Meta-Datos Dinámicos:** Configurar títulos, descripciones y etiquetas Open Graph (OG) para redes sociales en cada vista.
* **Comentarios Estratégicos:** Comentar la lógica de negocio compleja. Evitar comentarios obvios.
* **Archivo `README.md`:** Todo proyecto debe contar con un archivo de documentación con:
  1. Guía de instalación y ejecución local (Frontend y Backend).
  2. Estructura de carpetas.
  3. Variables de entorno requeridas (`.env.example`).
  4. Lista de endpoints principales de la API.