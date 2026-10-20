# 🧠 Plan Maestro de Arquitectura: Asistente Recepcionista Multi-Agente con IA para Violett Pilates

---

## 1. Visión y Objetivos del Proyecto

El objetivo es transformar el estudio **Violett Pilates** en un negocio autónomo y con atención 24/7 de nivel humano mediante un **Sistema Multi-Agente Inteligente**. 

No se trata de un chatbot simple de preguntas y respuestas basadas en árboles rígidos, sino de un **equipo coordinado de agentes especializados de IA** que colaboran entre sí, consultan la base de datos de Django en tiempo real, operan la agenda (3 camillas/reformers por turno), gestionan cobros, asisten a la dueña con reportes y coordinan de forma proactiva a las alumnas y al staff docente.

### Canales y Experiencia de Usuario
* **WhatsApp Conversacional Natural:** Una alumna puede hacer toda su gestión por WhatsApp (reservar, cancelar, consultar saldo, enviar comprobante de pago, pedir cambio de horario) exactamente igual que si usara la aplicación web.
* **Coordinación Docente:** Un profesor puede avisar que no puede dar una clase y el sistema busca reemplazo automáticamente entre los demás profesores calificados. Si nadie puede, reprograma o cancela el turno avisando a las alumnas.
* **Modo Dueña / Executive Assistant:** La dueña del estudio puede pedir métricas en lenguaje natural (*"¿Cuánto cobramos esta semana?", "¿Quiénes tienen clases pendientes?"*), agendar alumnas manualmente o pasar contactos de prospectos para que el asistente los contacte y los dé de alta.
* **Proactividad (Yield Management):** El sistema no solo espera pasivamente; monitorea la base de datos para detectar camillas vacías y escribe a listas de espera o alumnas frecuentes para llenar las 3 camillas de cada turno.

---

## 2. Evaluación Arquitectónica: ¿Cómo encaja en nuestra estructura tipo Lego?

Nuestra plataforma (**FireSeed Engine**) se caracteriza por su modularidad:
* `engine/backend/core/`: Modelos base de identidad, turnos, clases y reservas.
* `engine/backend/backend_core/hooks.py`: Registro pub/sub de eventos (`registry.register`, `registry.execute`).
* `engine/plugins/`: Módulos enchufables activados por configuración (`client-config.json`).
* `engine/plugins/comunicaciones/`: Ya cuenta con integración inicial a la WhatsApp Cloud API y servicio de emails.

### Comparativa de Opciones Estructurales

| Criterio | Opción A: Microservicio Independiente (FastAPI + LangGraph) | Opción B: Todo dentro de `comunicaciones` | Opción C (Recomendada): **Plugin `asistente` + Capa I/O en `comunicaciones`** |
| :--- | :--- | :--- | :--- |
| **Arquitectura** | Contenedor Docker separado, base de datos compartida o API REST interna. | Mezclar LLMs, prompts y herramientas dentro del plugin de mensajería básico. | **Arquitectura de dos capas Lego**: `comunicaciones` es el hardware/cable (Transporte) y `asistente` es el cerebro (Agentes). |
| **Acceso a Datos** | Lento / Redundante: requiere duplicar modelos o consultar todo vía endpoints HTTP. | Directo vía ORM, pero rompe el principio de responsabilidad única. | **Directo, rápido y transaccional**: usa el ORM de Django con locks atómicos para evitar sobreventa de cupos. |
| **Mantenibilidad** | Alta complejidad operativa (más contenedores, redes Docker, autenticación entre servicios). | Código espagueti (prompts mezclados con templates de email y webhooks). | **Limpio y Modular**: si un cliente no paga IA, se apaga el plugin `asistente` y el sistema sigue funcionando normalmente. |
| **Consumo de Recursos** | Alto (duplica workers de Python en la VPS). | Bajo. | **Óptimo**: comparte el runtime de Django existente con ejecución asíncrona. |

---

## 3. Topología de la Solución (Arquitectura en 2 Capas)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CAPA 1: TRANSPORTE (I/O)                        │
│                   (Plugin: plugins.comunicaciones)                     │
│                                                                        │
│   WhatsApp Webhook (Meta)  ──►  WhatsAppWebhookView                    │
│                                           │ Valida y Despacha          │
│                                           ▼ Evento                     │
│                             registry.execute('whatsapp_mensaje_recibido')│
└───────────────────────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   CAPA 2: INTELIGENCIA & MULTI-AGENTE                  │
│                     (Nuevo Plugin: plugins.asistente)                  │
│                                                                        │
│   Dispatcher Asíncrono ──► LangGraph StateGraph Execution               │
│                                                                        │
│         ┌───────────────────────────────────────────────────────┐      │
│         │              SUPERVISOR / TRIAGE ROUTER               │      │
│         │     (Identifica rol: Alumna, Profesor o Dueña)        │      │
│         └──────┬─────────────┬─────────────┬─────────────┬──────┘      │
│                │             │             │             │             │
│                ▼             ▼             ▼             ▼             │
│         ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │
│         │  Agente   │ │  Agente   │ │  Agente   │ │  Agente   │        │
│         │  Turnos   │ │ Finanzas  │ │Profesores │ │ Dirección │        │
│         │(Camillas) │ │ (Planes)  │ │(Suplentes)│ │ (Admin)   │        │
│         └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘        │
│               │             │             │             │              │
│               └─────────────┴──────┬──────┴─────────────┘              │
│                                    ▼                                   │
│                        Django ORM Tools & Services                     │
│                    (PostgreSQL: Turnos, Clases, Pagos)                 │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  CAPA 3: PROACTIVIDAD EN BACKGROUND                    │
│                      (Django APScheduler / Cron)                       │
│                                                                        │
│   Optimizador de Ocupación (cada 15 min):                              │
│   • Detecta turnos en próx. 24-48h con cupo < 3 camillas               │
│   • Consulta Alumnas Candidatas / Lista de Espera                      │
│   • Dispara mensaje proactivo de invitación por WhatsApp               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. ¿Por qué LangGraph es la herramienta perfecta?

Para un sistema empresarial con dinero y turnos de Pilates, frameworks de "enjambre autónomo libre" (como CrewAI o AutoGen puro) son peligrosos porque pueden entrar en bucles infinitos o tomar decisiones no deterministas.

**LangGraph** aporta:
1. **Determinismo basado en Grafos de Estado (*StateGraph*):** Se definen los nodos de los agentes y los bordes condicionales con precisión milimétrica.
2. **Memoria de Conversación Persistente en PostgreSQL:** Cada usuario tiene un hilo (`thread_id = número_whatsapp`), lo que permite pausar la conversación y retomarla horas después con todo el contexto intacto.
3. **Soporte de Human-in-the-Loop:** Si el agente no está 100% seguro de un comprobante de pago o de una situación médica, pausa la ejecución y solicita confirmación a la dueña antes de ejecutar la acción.
4. **Tool Calling Nativo:** Compatible con `gpt-4o-mini` y `claude-3-5-haiku`, ejecutando funciones Python con tipado estricto (Pydantic).

---

## 5. Especificación de los 5 Agentes Especializados

### 1. Agente Supervisor & Triaje (Front-Desk)
* **Objetivo:** Analizar el mensaje entrante, identificar quién habla (verificando el número en la base de datos de usuarios) y determinar la intención principal.
* **Personalidad:** Cordial, cálida, educada, con modismos naturales de Argentina (*"¡Hola Sofi! ¿Cómo estás?", "Dale, dejame que me fije los lugares disponibles"*).
* **Enrutamiento:**
  * Si el remitente es la dueña del estudio $\rightarrow$ Agente Dirección.
  * Si el remitente es un profesor registrado $\rightarrow$ Agente Profesores.
  * Si pide turnos, cupos, cambios o cancelaciones $\rightarrow$ Agente Turnos.
  * Si consulta precios, debe pagar o envía un comprobante $\rightarrow$ Agente Finanzas.
  * Si es una persona no registrada $\rightarrow$ Inicia flujo de bienvenida y alta.

---

### 2. Agente de Camillas y Grilla (Booking & Turnos)
* **Objetivo:** Gestionar la ocupación física del estudio bajo la regla de oro: **máximo 3 camillas de reformer por turno**.
* **Herramientas (Tools):**
  * `consultar_turnos_disponibles(fecha, rango_horario)`: Retorna turnos con cupo actual $> 0$.
  * `reservar_turno(alumno_id, turno_id)`: Valida saldo de créditos en la suscripción, genera la `Reserva` y descuenta el cupo con `select_for_update()` para evitar carreras de concurrencia.
  * `cancelar_turno(reserva_id)`: Aplica política de cancelación (e.g. reintegro de clase si cancela con más de 2 horas de anticipación).
  * `cambiar_turno(reserva_actual_id, nuevo_turno_id)`: Movimiento atómico de una reserva a otro bloque horario.

---

### 3. Agente Financiero y Membresías (Cobranzas)
* **Objetivo:** Gestionar planes, renovaciones y validar transferencias bancarias.
* **Herramientas (Tools):**
  * `consultar_estado_plan(alumno_id)`: Vencimiento, clases restantes y clases agendadas.
  * `generar_link_pago_mercadopago(plan_id, alumno_id)`: Genera link de cobro inmediato.
  * `obtener_datos_transferencia()`: Alias, CBU y titular del estudio.
  * `analizar_comprobante_transferencia(imagen_url)`: Utiliza visión multimodal de LLM para extraer fecha, monto, emisor y código de operación del comprobante y registrarlo como pendiente o acreditado.
  * `reactivar_plan_alumno(alumno_id, plan_id)`: Resetea los créditos y auto-agenda en sus horarios fijos (reutilizando el servicio que programamos en `plugins.recurrencias`).

---

### 4. Agente Coordinador de Profesores (Staff & Reemplazos)
* **Objetivo:** Manejar la comunicación interna con las instructoras y resolver ausencias imprevistas.
* **Flujo de Reemplazo Inteligente:**
  1. La profesora manda un mensaje: *"Chicas, el martes a las 17 hs tengo médico y no llego a dar la clase"*.
  2. El agente identifica el turno asignado a esa profesora para el martes a las 17:00 hs.
  3. Consulta qué otros profesores están registrados y no tienen clase asignada en ese bloque.
  4. Envía un WhatsApp individual a las candidatas: *"Hola Juli, ¿cómo estás? Cande no va a poder dar la clase de Reformer de este Martes 17:00 hs. ¿Tendrías disponibilidad para cubrirla?"*.
  5. La primera profesora que responda afirmativamente se le asigna el turno (`turno.profesor = nueva_profe`).
  6. El agente confirma a la nueva profesora, avisa a la profesora titular y envía un resumen a la dueña.
  7. Si pasan $X$ horas y nadie puede cubrir la clase, notifica con urgencia a la dueña para decidir si se cancela o si la toma ella.

---

### 5. Agente de Dirección / Dueña (Executive Assistant)
* **Objetivo:** Responder a comandos de gestión y reportes ejecutivos para la administración del estudio.
* **Capacidades:**
  * **Reportes en vivo:** *"Pasame el resumen de la semana"*, *"¿Cuántas alumnas vinieron hoy?"*, *"¿Cuánto facturamos este mes?"*.
  * **Agendado administrativo forzado:** *"Anotame a Laura Gómez en el turno de hoy a las 18 aunque no tenga créditos, arregló conmigo"*.
  * **Campañas de prospección:** *"Te paso estos 5 números de Instagram que pidieron info: [números]. Escribiles y guialos para registrarse"*. El agente redacta un mensaje inicial cálido y realiza el onboarding guiado por WhatsApp.

---

### 6. Agente Proactivo de Ocupación (Yield Optimization Worker)
* **Objetivo:** Asegurar que cada turno funcione al 100% de su capacidad (3 camillas ocupadas).
* **Frecuencia:** Tarea programada en `APScheduler` cada 15 a 30 minutos.
* **Lógica Proactiva:**
  * Detecta huecos disponibles en las próximas 24 a 48 horas.
  * Busca en la base de datos a alumnas con créditos activos que habitualmente asisten en ese horario o que están en lista de espera.
  * Envía una notificación suave de oportunidad:
    > *"¡Hola Cami! Se acaba de liberar una camilla para hoy a las 19:00 hs en Pilates Reformer. Como tenés clases disponibles en tu plan, ¿te gustaría que te reserve el lugar?"*
  * Si la alumna responde "Sí, por favor", el Agente de Turnos la reserva automáticamente sin intervención humana.

---

## 6. Estructura de Archivos del Nuevo Plugin

Siguiendo el estándar de arquitectura modular de nuestro repositorio:

```
engine/plugins/asistente/
├── __init__.py
├── backend/
│   ├── __init__.py
│   ├── apps.py                  # Registra listeners de hooks de comunicaciones
│   ├── models.py                # Sesiones de conversación, mensajes, auditoría
│   ├── urls.py                  # Endpoints administrativos para el panel React
│   ├── views.py                 # Configuración de prompts, historial de chat
│   ├── graph/                   # Orquestación con LangGraph
│   │   ├── __init__.py
│   │   ├── state.py             # Definición de AgentState
│   │   ├── graph_builder.py     # Nodos y bordes del grafo de LangGraph
│   │   ├── supervisor.py        # Nodo de enrutamiento y triaje
│   │   └── checkpointer.py      # Persistencia de memoria en PostgreSQL
│   ├── agents/                  # Agentes especializados
│   │   ├── __init__.py
│   │   ├── turnos_agent.py      # Agente de camillas y grilla
│   │   ├── finanzas_agent.py    # Agente de pagos y planes
│   │   ├── profesores_agent.py  # Agente de staff y reemplazos
│   │   ├── direccion_agent.py   # Agente de la dueña y reportes
│   │   └── proactivo_agent.py   # Lógica del optimizador de ocupación
│   ├── tools/                   # Tools de Django ORM
│   │   ├── __init__.py
│   │   ├── turnos_tools.py      # consultar_cupos, crear_reserva, etc.
│   │   ├── finanzas_tools.py    # crear_pago_mp, reactivar_plan, etc.
│   │   ├── profesores_tools.py  # buscar_suplentes, reasignar_turno, etc.
│   │   └── reportes_tools.py    # metricas_facturacion, asistencia_semanal
│   └── services/
│       ├── __init__.py
│       ├── vision_service.py    # OCR y extracción de comprobantes con LLM
│       └── dispatcher.py        # Encolador asíncrono para no trabar el webhook
```

---

## 7. Modelos de Base de Datos para el Asistente

Para que el sistema sea auditable y transparente:

1. **`ConversacionWhatsApp`**:
   * `telefono`: Número en formato E.164.
   * `usuario`: Llave foránea opcional a `Usuario` (se vincula automáticamente al identificar al alumno o profesor).
   * `rol_detectado`: `ALUMNO`, `PROFESOR`, `DUEÑA`, `DESCONOCIDO`.
   * `estado_sesion`: `ACTIVO`, `ESPERANDO_HUMANO`, `RESUELTO`.
   * `ultimo_contacto`: Timestamp.

2. **`MensajeWhatsApp`**:
   * `conversacion`: FK a `ConversacionWhatsApp`.
   * `direccion`: `ENTRANTE` o `SALIENTE`.
   * `agente_responsable`: Nombre del agente que respondió (e.g. `turnos_agent`, `finanzas_agent`).
   * `contenido`: Texto del mensaje.
   * `metadatos`: JSON con tokens consumidos, tools ejecutadas, IDs de turnos afectados.

3. **`RegistroAccionAgente`**:
   * Auditoría de cambios críticos (e.g. turno reservado por IA, plan reactivado por IA, reemplazo docente asignado por IA). Permite a la dueña ver en el panel exactamente qué hizo el asistente.

---

## 8. Seguridad, Prevención de Fallos y Human-in-the-Loop

1. **Prevención de Sobreventa de Camillas (Concurrencia):**
   * El límite de 3 camillas es innegociable. Cualquier reserva ejecutada por el agente utilizará transacciones atómicas de Django con `select_for_update()` en la fila del `Turno`, garantizando que nunca se reserven más de 3 lugares aunque dos personas escriban en el mismo segundo por WhatsApp y la web.
2. **Fraude en Transferencias Bancarias:**
   * El asistente analiza el comprobante con Visión (monto, fecha, ID de transacción). Si el monto coincide con el plan y el ID no fue utilizado antes, puede acreditar de forma preventiva o marcar el comprobante con aviso a la dueña: *"Recibí comprobante de Sofía por $X. ¿Aprobás la activación?"* con botones interactivos.
3. **Escalamiento a Humano:**
   * Si la alumna escribe *"Quiero hablar con una persona"* o el agente detecta que la consulta excede sus herramientas, el estado pasa a `ESPERANDO_HUMANO` y notifica a la dueña sin responder automáticamente.

---

## 9. Hoja de Ruta de Implementación (Roadmap por Fases)

### Fase 1: Cimientos y Conexión Asíncrona (Semana 1)
- [ ] Creación de la estructura del plugin `engine/plugins/asistente/`.
- [ ] Modificación de `plugins/comunicaciones/backend/views.py` para emitir el hook `whatsapp_mensaje_recibido`.
- [ ] Implementación de `dispatcher.py` para responder `HTTP 200` a Meta en menos de 1 segundo y procesar el agente en un hilo/worker secundario.
- [ ] Configuración del cliente LLM (`LangGraph` + `OpenAI` o `Anthropic`).

### Fase 2: Agente de Turnos y Camillas (Semana 2)
- [ ] Creación de tools de lectura y reserva de turnos en `turnos_tools.py`.
- [ ] Implementación del nodo de triaje y del `turnos_agent.py`.
- [ ] Pruebas reales por WhatsApp: consulta de grilla, reserva de clase con débito de crédito, cancelación y cambio de horario.

### Fase 3: Agente Financiero y Membresías (Semana 3)
- [ ] Tools de consulta de plan y generación de links de Mercado Pago.
- [ ] Integración del servicio de Visión para lectura de comprobantes de transferencia.
- [ ] Conexión con el servicio de `reactivar_plan` que construimos previamente.

### Fase 4: Coordinación de Profesores y Reemplazos (Semana 4)
- [ ] Reconocimiento de números de teléfono del staff de instructoras.
- [ ] Flujo de aviso de ausencia y búsqueda automática de reemplazos vía WhatsApp.
- [ ] Reasignación automática de profesor en el turno.

### Fase 5: Yield Manager Proactivo y Panel de Control (Semana 5)
- [ ] Tarea programada en `APScheduler` para escaneo de huecos libres y contacto con lista de espera.
- [ ] Modo Directora: comandos de reportes y alta de contactos para la dueña.
- [ ] Pantalla en el panel React (`/admin/asistente`) para monitorear conversaciones, auditoría de acciones y ajuste de prompts.
