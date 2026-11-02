---
name: fireseed-methodology
description: Metodología oficial de arquitectura, ingeniería de software y desarrollo de FireSeed. Define el stack tecnológico (React/Vite, Django, PostgreSQL, Docker, LangGraph), la arquitectura modular basada en plugins ('legos' / Microkernel), el diseño atómico frontend, la separación de configuración multi-cliente (Config-Driven Engine), y la arquitectura de agentes de IA con LangGraph (orquestación en grafo, Human-in-the-Loop, espera activa, centinela debugger y degradación elegante). Usa esta skill siempre que vayas a diseñar, codificar, extender o refactorizar cualquier parte del ecosistema de FireSeed para mantener absoluta coherencia arquitectónica.
---

# 🚀 FireSeed — Metodología Oficial de Ingeniería y Arquitectura

Bienvenido al manual maestro de desarrollo de **FireSeed** (*"Fueling Innovation"*). 
Este documento define los principios arquitectónicos, el stack tecnológico estándar, los patrones de diseño formales y la metodología de orquestación de inteligencia artificial que rigen todas las aplicaciones construidas por FireSeed.

Cualquier agente de IA, desarrollador o nuevo chat que continúe el trabajo en este repositorio debe seguir estas directrices con rigor para mantener la integridad, escalabilidad y excelencia técnica del sistema.

---

## 🏛️ 1. Glosario de Ingeniería: Los "Nombres Reales" de la Metodología

Cuando en el día a día decimos que armamos las cosas como **"piezas de Lego"**, en la literatura formal de ingeniería de software estamos aplicando los siguientes patrones y principios:

| Metáfora cotidiana | Nombre Técnico Profesional | ¿Qué significa en la práctica? |
| :--- | :--- | :--- |
| **"Piezas de Lego" / Plugins** | **Microkernel Architecture (Arquitectura de Plugins)** | El núcleo del sistema (*Engine Core*) es mínimo y estable. Todas las funciones de negocio (Reservas, Finanzas, Asistente IA, Notificaciones) son plugins desacoplados que se pueden conectar, desconectar o reemplazar sin tocar el Core. |
| **"Piezas visuales reutilizables"** | **Atomic Design / Component-Driven Development (CDD)** | Construir la interfaz de usuario en capas estrictas: Átomos (`Button`, `Badge`), Moléculas (`SearchInput`), Organismos (`ClassCard`, `Sidebar`) y Vistas (`AgendaAdmin`). |
| **"Un solo motor para muchas marcas"** | **Config-Driven Architecture (Arquitectura Dirigida por Configuración)** | El código base no tiene nombres de clientes hardcodeados. El mismo motor ejecuta *Violett Pilates*, *Violett Estética* o un nuevo cliente cambiando únicamente su archivo `client-config.json`, su paleta de tokens y sus reglas de negocio. |
| **"Multi-inquilino seguro"** | **Multi-Tenancy con Aislamiento por Contenedor** | Cada cliente corre en su propio contenedor Docker y con su propia base de datos PostgreSQL, garantizando aislamiento total de datos y rendimiento. |
| **"Oficina virtual de bots"** | **Stateful Multi-Agent DAG (Grafo Dirigido Acíclico con Estado)** | No usamos un prompt gigante con un chatbot genérico. Usamos **LangGraph** para modelar un equipo de agentes especializados, donde un nodo Router hace el triaje y delega a un agente específico con memoria compartida (`AgentState`). |
| **"Preguntarle a Deby si quiso decir X"** | **Human-in-the-Loop (HITL) con Coincidencia Fonética** | Ante ambigüedad (errores de ortografía o transcripción de audio), el agente suspende la ejecución, presenta candidatos numerados y reanuda la operación pendiente al recibir la confirmación humana. |
| **"Si se cae un modelo, entra otro"** | **Graceful Degradation / Resilience Cascade (Cascada de Resiliencia)** | Cascada de conmutación por fallos: Gemini 2.5 Flash -> Groq Llama 3.3 -> OpenAI -> Simulador Heurístico Local. El sistema nunca se apaga. |
| **"Seguridad de la dueña"** | **Zero-Trust Security Model (Modelo de Confianza Cero)** | Nadie puede ejecutar comandos administrativos ni ver finanzas por afirmar ser la dueña. Se verifica criptográficamente el identificador de la línea autorizada (`5491157691786`). |

---

## 📐 2. Principios SOLID Aplicados en FireSeed

* **S (Single Responsibility Principle - Responsabilidad Única):**
  * *Frontend:* Un componente solo renderiza; la lógica HTTP reside en hooks (`useTurnos`, `useConversaciones`).
  * *Backend:* Las vistas (`views.py`) son delgadas; la lógica de negocio compleja habita en servicios (`services.py`).
  * *IA:* Cada agente en LangGraph tiene un único dominio (Turnos, Finanzas, Profesores, Dirección).
* **O (Open/Closed Principle - Abierto/Cerrado):**
  * El sistema está **abierto a extensión** (crear un plugin en `engine/plugins/nuevo_modulo/`) pero **cerrado a modificación** (no se tocan los archivos del Core para agregar una funcionalidad).
* **L (Liskov Substitution Principle - Sustitución de Liskov):**
  * Todo plugin cumple el contrato estándar de `PLUGIN_SPEC.md` (`routes.tsx` en frontend, `apps.py` / `urls.py` en backend). Cualquier plugin puede ser activado o desactivado limpiamente.
* **I (Interface Segregation Principle - Segregación de Interfaces):**
  * Los componentes y herramientas solo exponen los parámetros mínimos indispensables que sus consumidores necesitan.
* **D (Dependency Inversion Principle - Inversión de Dependencias):**
  * El Core nunca importa directamente un plugin. El Core depende de abstracciones (`plugin_loader.py` en backend y `pluginLoader.ts` en frontend) que leen `client-config.json`.

---

## 🛠️ 3. Stack Tecnológico Estándar

### Frontend
* **Core:** React 19 / Vite / TypeScript (Modo estricto, **prohibido `any`**).
* **Estilos:** Tailwind CSS con tokens de diseño dinámicos (`primary-main`, `primary-light`, `accent-gold`, etc.).
* **Animaciones:** Framer Motion (microinteracciones de 200ms a 400ms, estética fluida estilo Apple/Emil Kowalski).
* **Iconografía & Feedback:** Lucide React, Sonner (toasts).
* **Consumo de API:** Axios con interceptores de autenticación y manejo de errores.

### Backend
* **Framework:** Python 3.12+, Django 4.2+ / Django REST Framework.
* **Base de Datos:** PostgreSQL 15 con restricciones a nivel DB (`CheckConstraint`, `UniqueConstraint`), borrado lógico (`is_active = False`) e índices optimizados (`db_index=True`).
* **Concurrencia:** Bloqueos atómicos (`@transaction.atomic`) para evitar condiciones de carrera (Race Conditions) al apartar camillas o descontar créditos de planes.
* **Fechas y Horarios:** Almacenamiento en UTC (`timezone.now()`) y renderizado en hora local de Argentina (`America/Argentina/Buenos_Aires`).

### Inteligencia Artificial & Orquestación
* **Orquestador:** LangGraph + LangChain Core.
* **LLM Principal:** Google Gemini (`gemini-2.5-flash` / `gemini-2.0-flash`) con temperatura ultra-baja (`0.1`) para precisión matemática y cero alucinaciones.
* **LLM Fallbacks:** Groq (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`), OpenAI (`gpt-4o-mini`).
* **Canal:** WhatsApp Cloud API / Microservicio Meta Webhook con procesamiento de audio y texto.

### Infraestructura & DevOps
* **Virtualización:** Docker + Docker Compose.
* **Proxy Inverso:** Nginx con compresión gzip, caché de estáticos y soporte HTTPS.
* **Automatización:** Script de despliegue atómico [`deploy.sh`](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/deploy.sh) con limpieza automática de imágenes huérfanas (`docker image prune -f`).

---

## 🧩 4. Estructura de la Arquitectura Modular ("El Motor y los Plugins")

El proyecto se divide de forma limpia en tres capas:

```
├── config_pilates/               <-- CONFIGURACIÓN DEL CLIENTE (Tokens, Plugins activos, Reglas)
│   ├── client-config.json        <-- Define qué plugins se cargan y las variables del negocio
│   ├── brand_persona.md          <-- Voz, tono y personalidad de la marca para la IA
│   └── reglas_negocio.md         <-- Políticas de cancelación (ej. 25hs), turnos y precios
│
├── engine/                       <-- EL MOTOR UNIVERSAL (Reutilizable para cualquier cliente)
│   ├── backend/                  <-- Core Django (Auth, Usuarios, Enrutador de plugins)
│   ├── frontend/                 <-- Core React (Layouts, Routing dinámico, Slots inyectables)
│   └── plugins/                  <-- LOS "LEGOS" (Módulos independientes de negocio)
│       ├── asistente/            <-- Bot de WhatsApp + LangGraph + Agente Centinela
│       ├── comunicaciones/       <-- Centro de mensajes WhatsApp en vivo y auditoría de emails
│       ├── membresias/           <-- Planes, abonos recurrentes y suscripciones
│       └── agenda/               <-- Grilla semanal, camillas Reformer y asistencias
│
└── proxy/                        <-- Nginx Gateway y distribución de dominios
```

### Contrato de un Plugin (`PLUGIN_SPEC.md`)
Cada módulo dentro de `engine/plugins/<nombre>/` debe ser autosuficiente:
1. **`backend/`:** Contiene sus propios `models.py`, `views.py`, `urls.py`, y `services.py`. Se registra automáticamente en Django vía `plugin_loader.py`.
2. **`frontend/routes.tsx`:** Exporta su contrato de rutas:
   * `publicRoutes`: Rutas accesibles sin login.
   * `roleRoutes`: Rutas según rol (`CLIENTE`, `PROFESOR`, `ADMIN`).
   * `adminRoutes`: Vistas del panel de negocio.
   * `adminSidebarItems`: Botones inyectados en la barra lateral.
   * `slots`: Componentes inyectados en ranuras visuales (`<PluginSlot name="..." />`).

---

## 🤖 5. Arquitectura del Asistente Virtual (LangGraph & Multi-Agente)

El asistente de Violett Pilates no es un prompt plano; es una **oficina virtual organizada en un Grafo de Agentes**:

```
[ WhatsApp ] ──► [ Router Triaje (0ms) ]
                         │
        ┌────────────────┼────────────────┬────────────────┐
        ▼                ▼                ▼                ▼
  [ Recepcionista ]  [ Turnos ]      [ Finanzas ]     [ Dirección ] (Solo Deby)
  (Bienvenida/FAQ)  (Cupos/Camillas) (Planes/CBU)    (Reportes/Altas/Fichas)
                         │                │                │
                         └────────────────┼────────────────┘
                                          ▼
                             [ Ejecutor de Tools DB ] ──► (Aviso "Aguardame...")
                                          │
                                          ▼
                             [ Centinela / Debugger ] ──► (Bitácora & Ticket #ERR)
```

### Reglas de Oro de los Agentes
1. **Voseo Argentino y Empatía Humana:** Usar 'vos', 'querés', 'fijate', 'sentite'. Hablar con calidez a personas adultas, jamás como un contestador automático.
2. **Cero Repetición de Saludos:** Si la conversación ya está iniciada, responder directamente al grano. Solo decir "¡Hola!" en el primerísimo contacto.
3. **Espera Activa:** Si una consulta va a demorar consultando la base de datos, un hilo paralelo envía de inmediato: *"✦ Aguardame un segundito que ya me fijo en el sistema..."*.
4. **Coincidencia Fonética y Human-in-the-Loop:** Usar `SequenceMatcher` para tolerar audios y nombres mal escritos (*"marzuk"* -> *Laila Marzzuck*), pidiendo confirmación numerada antes de ejecutar acciones en la agenda.
5. **Agente Centinela (Debugger):** Si ocurre una excepción o se agota la cuota del LLM:
   * A Débora le explica el diagnóstico técnico con un Ticket `#ERR-xxxx`.
   * A las alumnas les responde con calma y cordialidad.
   * Registra el fallo en `RegistroErrorIA` y lo publica en la pestaña de diagnóstico del panel web.

---

## 🚀 6. Buenas Prácticas de Despliegue y Git

* **Commits Semánticos:** Usar prefijos claros (`feat:`, `fix:`, `refactor:`, `style:`, `docs:`).
* **Firma en Código:** Cada archivo nuevo debe incluir la firma:
  * Python: `# Developed by FireSeed - Fueling Innovation`
  * TypeScript / React: `/* Developed by FireSeed - Fueling Innovation */`
* **Despliegue Seguro:** Ejecutar [`deploy.sh`](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/deploy.sh) en el servidor. Nunca pasar `--seed` en producción rutinaria para resguardar las contraseñas de las usuarias reales.
