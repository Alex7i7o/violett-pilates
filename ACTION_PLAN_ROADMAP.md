# 🚀 Plan de Acción y Hoja de Ruta de Desarrollo (Roadmap) — FireSeed
## Proyecto: Aplicación Web de Reservas y Gestión para Estudio de Pilates

/* Developed by FireSeed - Fueling Innovation */

---

## 📋 Resumen del Plan
Este plan de acción desglosa el desarrollo de la aplicación en **3 Fases Secuenciales**, diseñadas para construirse de manera limpia mediante prompts directos para **Google Antigravity**. Cada paso contiene criterios de aceptación claros para validar que no existan errores antes de avanzar a la siguiente etapa.

---

## 🛠️ FASE 1: Backend Base, Arquitectura de Datos y Autenticación

### Paso 1.1: Inicialización del Repositorio y Entorno Backend
* **Acción:** Crear la estructura del proyecto Django, configurar variables de entorno (`.env`) y la conexión a PostgreSQL.
* **Archivos Afectados:** `settings.py`, `.env.example`, `requirements.txt`.
* **Criterio de Aceptación:** Proyecto corriendo en local con PostgreSQL conectado y firmas de FireSeed en archivos principales.

### Paso 1.2: Modelos de Base de Datos y Migraciones (ORM)
* **Acción:** Implementar las entidades de `DATABASE_SCHEMA.md` (`configuracion_global`, `usuarios`, `planes`, `suscripciones`, `clases`, `turnos`, `recurrencias`, `reservas`).
* **Archivos Afectados:** `models.py`, migraciones de Django.
* **Criterios Clave:**
  * Uso de `UUID` en identificadores clave.
  * `CheckConstraint` y `UniqueConstraint` para asegurar límites de cupos y no duplicidad.
  * Implementación de campos `is_active` para Soft Delete.

### Paso 1.3: Panel de Administración (Django Admin)
* **Acción:** Registrar y personalizar el panel de administración de Django para la gestión de `ConfiguracionGlobal` (parámetros de cupos 3/2, 24hs, 25hs, 30 días) y administración manual de agenda/planes.
* **Archivos Afectados:** `admin.py`.
* **Criterio de Aceptación:** El administrador puede editar los parámetros globales y crear/modificar turnos y usuarios de forma visual.

### Paso 1.4: Autenticación, Google OAuth 2.0 y Tokens JWT
* **Acción:** Configurar `django-allauth` y `dj-rest-auth` para habilitar el registro/login tradicional y **Google Sign-In**.
* **Archivos Afectados:** `views.py`, `serializers.py`, `urls.py`.
* **Criterio de Aceptación:** Generación y validación exitosa de JWT tras autenticarse con Google.

---

## 🎨 FASE 2: Frontend, Sistema de Diseño "FireSeed" y Dashboard Interactivo

### Paso 2.1: Setup de React, TypeScript, Tailwind y Design Tokens
* **Acción:** Configurar el proyecto Frontend en React con TypeScript, Tailwind CSS y Framer Motion segun `RULES.md`.
* **Archivos Afectados:** `tailwind.config.js`, `src/styles/globals.css`.
* **Criterio de Aceptación:** Estilos globales configurados, variables de color/fuente mapeadas y banner de bienvenida de FireSeed en la consola del navegador.

### Paso 2.2: Sistema de Componentes "Piezas de Lego" (UI Kit)
* **Acción:** Desarrollar componentes atómicos reutilizables: `Button`, `Modal`, `Card`, `Badge`, `CalendarGrid`, `InputField`.
* **Archivos Afectados:** `src/components/ui/`.
* **Regla:** Animaciones suaves con `framer-motion` (duración entre 200ms y 400ms).

### Paso 2.3: Dashboard del Cliente
* **Acción:** Construir la vista principal del alumno mostrando:
  * Estado del Plan Activo (clases restantes, fecha de vencimiento).
  * Próximas Clases Agendadas.
  * Historial de Asistencia ("Clases Tomadas").
* **Archivos Afectados:** `src/pages/Dashboard.tsx`, Custom Hook `useClientProfile.ts`.

### Paso 2.4: Módulo de Calendario y Reserva de Turnos
* **Acción:** Desarrollar la grilla interactiva de agenda semanal/diaria.
* **Funcionalidad:**
  * Mostrar turnos con cupos disponibles en tiempo real.
  * Opción de elegir **Turno Puntual** o **Turno Recurrente** (fijo semanal).
  * Modal interactivo para cancelación: *"¿Cancelar solo esta semana o todas las sesiones futuras?"*.
* **Archivos Afectados:** `src/components/booking/`, Custom Hook `useBookings.ts`.

---

## ⚙️ FASE 3: Lógica de Negocio, Automatizaciones (25hs) y Bot de WhatsApp

### Paso 3.1: Capa de Servicios de Negocio (`services.py`)
* **Acción:** Implementar la lógica transaccional de reservas y cancelaciones.
* **Reglas a Codificar:**
  * Permitir modificación/cancelación libre si faltan **> 24 horas**.
  * Bloquear o penalizar cancelación si faltan **< 24 horas**.
  * Descuento automático del crédito del plan cuando la fecha/hora del turno transcurre.
  * Protección de cupo recurrente (el horario semanal queda bloqueado a nombre del alumno hasta el vencimiento sin renovación).
* **Archivos Afectados:** `services.py` con decoradores `@transaction.atomic`.

### Paso 3.2: Motor de Evaluación Automática a las 25 Horas (Celery / Cron Jobs)
* **Acción:** Programar la tarea asíncrona que se ejecuta exactamente 25 horas antes de cada clase.
* **Lógica Evaluadora:**
  * **Si inscriptos < 2:** Cancelar clase automáticamente, devolver crédito al alumno y marcar turno como `CANCELADO`.
  * **Si inscriptos == 2:** Disparar evento de "Alerta de Cupo Libre" (queda 1 lugar).
  * **Si inscriptos >= 2:** Disparar evento de "Recordatorio de Asistencia".
* **Archivos Afectados:** `tasks.py`, `celery.py`.

### Paso 3.3: Integración de WhatsApp API y Bot Inteligente (Gem)
* **Acción:** Conectar los eventos del backend con la API de WhatsApp mediante webhooks.
* **Escenarios Notificados:**
  1. Cancelación automática de clase (25hs antes).
  2. Alerta de vacante disponible (25hs antes).
  3. Recordatorio de clase del día siguiente.
  4. Alerta de última clase restante del plan.
  5. Alerta preventiva a 5 días del vencimiento del plan.
  6. Aviso de liberación de horario recurrente por falta de renovación.
* **Archivos Afectados:** `services/whatsapp_service.py`.

---

## 📌 Guía de Prompts para Google Antigravity (Paso a Paso)

Usa esta secuencia de órdenes con Antigravity para construir el proyecto sin desviaciones:

### 🚀 Prompt #1 (Para iniciar la Fase 1)
> *"Hola Antigravity. Vamos a iniciar el desarrollo de la app de Pilates para FireSeed. Te adjunto los archivos `RULES.md`, `SRS.md` y `DATABASE_SCHEMA.md`. 
> Tu objetivo actual es ejecutar la **FASE 1 (Pasos 1.1 y 1.2)**: Crea el proyecto Django con soporte para PostgreSQL, define los modelos en `models.py` según `DATABASE_SCHEMA.md` y genera las migraciones iniciales. No generes nada de Frontend aún. Confírmame cuando las migraciones estén aplicadas."*

### 🚀 Prompt #2 (Para la Fase 1.3 y 1.4)
> *"Excelente. Ahora ejecuta los **Pasos 1.3 y 1.4**: Configura el Django Admin para administrar `ConfiguracionGlobal` y habilita la autenticación JWT con `django-allauth` para permitir login con Google OAuth 2.0 y correo. Muestra cómo probar la autenticación."*

### 🚀 Prompt #3 (Para iniciar la Fase 2)
> *"Avanzamos a la **FASE 2 (Pasos 2.1 y 2.2)**: Configura la estructura inicial de React con TypeScript, Tailwind CSS y Framer Motion siguiendo los Design Tokens y la firma de FireSeed especificados en `RULES.md`. Crea la carpeta de componentes atómicos UI (`Button`, `Modal`, `Card`, `Badge`)."*

### 🚀 Prompt #4 (Para la Fase 2.3 y 2.4)
> *"Construye el **Dashboard del Cliente y la Grilla de Reservas (Pasos 2.3 y 2.4)**. Crea los Custom Hooks `useClientProfile` y `useBookings` para conectar con la API de Django y maneja los estados de reserva puntual y recurrente."*

### 🚀 Prompt #5 (Para la Fase 3)
> *"Por último, ejecuta la **FASE 3**: Implementa `services.py` con transacciones atómicas para las cancelaciones a 24hs, el Cron Job de evaluación a las 25hs en `tasks.py` y el servicio de notificaciones por WhatsApp. Asegúrate de cubrir todos los disparadores descritos en `SRS.md`."*
