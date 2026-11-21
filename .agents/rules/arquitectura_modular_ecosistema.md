# Regla de Oro: Arquitectura Modular (Microkernel & Config-Driven)

Todo el software desarrollado bajo el ecosistema de FireSeed responde al patrón de arquitectura **Microkernel (SaaS Modular desacoplado por plugins)**. 

Para asegurar escalabilidad industrial, 0% de código duplicado y aislamiento absoluto entre clientes y marcas, **TODOS LOS AGENTES DE IA DEBEN SEGUIR ESTAS LEYES ARQUITECTÓNICAS:**

---

### 1. El Núcleo (Core) es Intocable por Lógica de Negocio
* Las carpetas `engine/backend/core/` y `engine/frontend/src/core/` solo contienen utilidades universales agnósticas (autenticación base, middleware de seguridad, RBAC, auditoría de transacciones y enrutador maestro).
* **Prohibido:** Jamás agregues reglas de negocio específicas de una marca (como Pilates, Estética o Clientes B2B) dentro del Core.

---

### 2. Desarrollo en Plugins Independientes ("Legos")
* Toda funcionalidad de negocio vive estrictamente dentro de un plugin aislado:
  * Backend: `engine/plugins/<nombre_plugin>/`
  * Frontend: `engine/frontend/src/plugins/<nombre_plugin>/`
* Cada plugin debe operar como un Lego autocontenido con sus propios modelos de base de datos, serializadores, endpoints (`urls.py`), vistas y rutas de frontend (`routes.tsx`).

---

### 3. Configuración en Tiempo de Compilación (Config-Driven)
* El comportamiento, visibilidad y activación de módulos por marca se define exclusivamente mediante `client-config.json` (o variables de entorno inmutables en tiempo de build).
* **Compilación Condicional:** Si un plugin no está activo en el `client-config.json` de un cliente, su código y sus rutas no deben cargarse en el bundle final.

---

### 4. Aislamiento Físico de Datos
* Cada vertical de negocio cuenta con su propia base de datos PostgreSQL independiente en Docker (`docker-compose.yml`).
* Jamás cruces consultas directas entre bases de datos de diferentes clientes; cualquier interacción entre sistemas debe realizarse mediante contratos de API RESTful protegidos por tokens criptográficos.

---

### 5. Agentes de IA: Orquestación Determinista en LangGraph
* Todo flujo de IA debe implementarse como un grafo con estado (`StateGraph`) en LangGraph con nodos bien delimitados.
* **Seguridad Zero-Trust:** Ningún agente ejecuta acciones destructivas o transacciones de dinero sin validación criptográfica o confirmación fonética humana (*Human-in-the-Loop*).
* **Resiliencia en Cascada:** Todo agente debe contar con fallback multimodelo (Gemini Flash → Groq Llama 3.3 → Heurístico Local) para garantizar 100% de disponibilidad.
