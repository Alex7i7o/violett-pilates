# Auditoría de Consumo y Estrategia de Optimización de Costos de IA (FinOps LLM)
**Proyecto:** Violett Pilates — Asistente Autónomo de WhatsApp & Gestión Ejecutiva  
**Fecha de Análisis:** Noviembre 2026  

---

## 1. Diagnóstico Real de tus 3 Capturas de Google AI Studio

Al analizar en conjunto las tres pantallas de tu consola (**Uso**, **Tokens por Modelo** y **Gasto de USD $0.80 / $0.92 en 8 días de actividad**), surge un hallazgo técnico fundamental que cambia por completo la estimación:

### A. ¿Por qué 8 días de pruebas con la Dueña gastaron ~$0.92 USD?

En la **Imagen 2 (Uso por modelo - Gemini 3.8 Flash)** se observa que en el día pico:
- **Solicitudes exitosas a la API:** ~42 peticiones.
- **Tokens de entrada consumidos ese mismo día:** **~530.000 tokens (530K)** y **~26.000 tokens de salida**.

Si dividimos los tokens entre las peticiones:
$$\frac{530.000 \text{ tokens}}{42 \text{ solicitudes}} \approx \mathbf{12.619 \text{ tokens de entrada por cada solicitud individual}}$$

**¿Por qué cada llamada de la Dueña pesaba ~12.600 tokens?**
1. **El peso de las 42 Herramientas (`DIRECCION_TOOLS`):**
   El agente de la Dueña (`agente_direccion`) tiene conectadas **42 herramientas administrativas** (facturación, agenda, esquemas, fichas, profesores, pagos, métricas, etc.).
   Cuando un modelo usa `bind_tools(DIRECCION_TOOLS)`, LangChain serializa los **42 esquemas JSON completos + todas las descripciones (docstrings)** y los envía por red en **cada petición**. Eso representa unos **~8.500 tokens fijos** en cada llamada.
2. **Doble viaje por cada mensaje (Ciclo ReAct de LangGraph):**
   Cuando la dueña pide algo (ej: *"Pasame la agenda de hoy"*), el flujo hace **2 llamadas** al modelo:
   - **Llamada 1:** Envía el System Prompt + Historial + las 42 herramientas (**~12.000 tokens**) para que el modelo decida qué función ejecutar.
   - **Llamada 2:** Ejecuta la función en la base de datos y **vuelve a llamar al modelo** enviando otra vez el System Prompt + Historial + las 42 herramientas + el resultado de la función (**~13.500 tokens**) para redactar la respuesta final.
   - **Resultado:** Un solo mensaje de WhatsApp de la dueña consume **~25.500 tokens**.
3. **Pruebas intensivas de Visión (Fotos de Fichas y Comprobantes):**
   Durante estos días estuvimos probando repetidamente fotos de alta resolución (fichas manuscritas complejas como las de Luz y Norma) y reintentos de desarrollo.
4. **Fallo de Groq (110 errores `404 NotFound` en la Imagen 1):**
   Como la clave de Groq arrojó error `404 model_not_found`, **el 100% del tráfico cayó directamente sobre Google Gemini Pago**, en lugar de ser absorbido gratis por Groq.
5. **Ahorro por Caché en $0.00 (Imagen 3):**
   En la tercera captura figura **`Costo: $0.80 - Ahorro: $0.00`**, lo que indica que no se estaba aplicando caché de contexto ni filtrado dinámico de herramientas.

---

### B. ¿Por qué el tráfico de las Alumnas cuesta 6 veces menos que el de la Dueña?

Es muy común pensar: *"Si 1 sola persona (la dueña) gastó $1 USD en 8 días, entonces 50 alumnas van a gastar $50 USD"*. **En esta arquitectura, eso NO ocurre así**, por dos razones técnicas:

| Característica | Rol `DUENA` (`agente_direccion`) | Rol `ALUMNA` (`agente_turnos` / `finanzas`) |
| :--- | :--- | :--- |
| **Cantidad de Herramientas adjuntas** | **42 herramientas** (~8.500 tokens fijos/llamada) | **4 herramientas** (~700 tokens fijos/llamada) |
| **Complejidad del System Prompt** | ~2.500 tokens (reglas de negocio, auditoría, fichas) | ~500 tokens (recepción y reservas) |
| **Consumo promedio por mensaje** | **~25.000 a 35.000 tokens** | **~2.500 a 4.000 tokens** (8 veces menor) |
| **Frecuencia de uso por persona** | Intensa (decenas de comandos diarios de gestión) | Baja (1 o 2 veces por semana para reprogramar o pagar) |

Una alumna promedio en un estudio de Pilates ya tiene su **horario fijo semanal**. Solo escribe por WhatsApp cuando:
1. Necesita cancelar o reprogramar una clase puntual (1 o 2 veces al mes).
2. Envía el comprobante de pago a principio de mes (1 vez al mes).
3. Un prospecto nuevo pregunta precios y horarios (3 o 4 mensajes).

---

## 2. ¿Cómo resuelven esto otras empresas en Producción para gastar un 90% menos?

En la industria de agentes de IA sobre WhatsApp (clínicas, gimnasios, estudios boutique, SaaS), nadie envía todas las herramientas ni llama al LLM más caro en cada mensaje. Se aplican **6 patrones de arquitectura (LLM FinOps)**:

```mermaid
flowchart TD
    MSG[Mensaje Entrante WhatsApp] --> DEB[1. Debouncer / Agrupador 2s\nUne ráfagas de mensajes en 1 solo]
    DEB --> FAST{2. Fast-Path Determinístico\n¿Es saludo, alias, precio o 'Confirmar'?}
    
    FAST -->|Sí - 45% de los casos| PY[Respuesta instantánea en Python\nCosto: $0.00 USD | 0 tokens]
    FAST -->|No - Requiere IA| ROUTER[3. Sub-Router de Herramientas\nSelecciona solo 5 tools en vez de 42]
    
    ROUTER --> TIER{4. Enrutamiento por Modelo}
    TIER -->|Consulta Estándar| FREE[Groq LPU Gratis / Gemini Flash-Lite\nCosto: $0.00 o $0.0001]
    TIER -->|Ficha Manuscrita Compleja| PRO[Gemini 2.5 / 3.8 Flash Vision]
    
    FREE --> EXEC[5. Ejecución de Tool con Return-Direct\nEvita la 2da llamada al LLM]
    PRO --> EXEC
```

### Solución 1: Selección Dinámica de Herramientas (*Dynamic Tool Filtering / Sub-Routing*)
* **El problema actual:** Mandar las 42 herramientas de la dueña en cada llamada cuesta ~17.000 tokens por mensaje (ida y vuelta).
* **Cómo se resuelve:** Antes de llamar al LLM, una función en Python (0ms, $0 costo) mira qué palabras tiene el mensaje de la dueña y **le adjunta al LLM únicamente las 4 a 6 herramientas de esa categoría**:
  * Si dice *"facturación"*, *"plata"*, *"ingresos"* ➔ Solo carga las **4 tools de Reportes**.
  * Si dice *"esquema"*, *"profe"*, *"reemplazo"* ➔ Solo carga las **5 tools de Profesores/Esquema**.
  * Si dice *"ficha"*, *"asistencia"*, *"créditos"*, *"plan"* ➔ Solo carga las **6 tools de Membresías/Fichas**.
  * Si dice *"agenda"*, *"anotá"*, *"cancelá"*, *"mové"* ➔ Solo carga las **7 tools de Agenda**.
* **Impacto:** El consumo de la dueña baja automáticamente de **~25.000 tokens a ~3.500 tokens por mensaje** (**85% de ahorro inmediato**).

### Solución 2: Cortocircuito Post-Herramienta (*`return_direct` / Bypass de 2da Llamada*)
* **El problema actual:** Cuando una herramienta de Python se ejecuta (por ejemplo, `obtener_reporte_facturacion` o `consultar_agenda_completa_dia`), la función **ya devuelve el texto hermoso con emojis, viñetas y formato WhatsApp**. Sin embargo, LangGraph vuelve a llamar al LLM pasándole todo el historial y las 42 herramientas solo para que el LLM repita ese mismo texto.
* **Cómo se resuelve:** Si la herramienta ejecutada ya entrega una respuesta final auto-contenida, el grafo **corta el ciclo (`END`) y envía el texto directo sin volver a llamar al LLM**.
* **Impacto:** **Reduce a la mitad (50%)** la cantidad de llamadas a la API y los tokens consumidos en cada operación con herramientas.

### Solución 3: *Fast-Path* Determinístico (Cero IA para mensajes predecibles)
* **Cómo lo hacen las grandes plataformas:** El 40% al 50% de los mensajes de WhatsApp no necesitan razonamiento neuronal:
  * Saludos iniciales (`"Hola"`, `"Buen día"`, `"Buenas tardes"`).
  * Agradecimientos (`"Gracias"`, `"Genial, nos vemos"`, `"Bárbaro"`).
  * Confirmaciones de botones o propuestas (`"Confirmar"`, `"Sí"`, `"Cancelar"`).
  * Solicitud de datos estáticos (`"Pasame el alias"`, `"¿Dónde queda el estudio?"`, `"¿Cuánto sale el plan de 8 clases?"`).
* **Impacto:** Se responden desde código Python en 10 milisegundos con **0 tokens y $0.00 USD**.

### Solución 4: *Model Tiering* (Usar Modelos "Lite" o Gratuitos para texto y dejar el Grande para Fotos)
* En tu captura de Google AI Studio tenés habilitados:
  * **`Gemini 2.5 Flash Lite` y `Gemini 2.0 Flash Lite`:** Son los modelos ultrarrápidos de Google diseñados específicamente para bots de alto volumen. Cuestan una fracción mínima (**~$0.075 por millón de tokens**, es decir, **13 veces más baratos** que los modelos pesados).
  * **Groq Cloud (Free Tier):** Con una API Key activa de Groq (`llama-3.3-70b-versatile`), las consultas de texto tienen costo **$0.00 USD** hasta 1.000 peticiones diarias.
* **Estrategia ideal:**
  1. **Texto diario (Alumnas y Dueña):** Groq Gratis ➔ Fallback a `Gemini 2.5 Flash Lite`.
  2. **Visión de Fichas Manuscritas en Papel:** Directo a `Gemini 2.5 Flash` / `Gemini 3.8 Flash` (donde sí necesitamos máxima agudeza visual y sólo se usa cuando suben una foto).

### Solución 5: Compresión de Esquemas (*Tool Docstring Minification*)
* Acortar las descripciones internas (`docstrings`) de cada `@tool` a 1 sola oración concisa. El LLM entiende perfectamente qué hace `consultar_agenda_completa_dia(fecha_str)` sin necesidad de un párrafo de 120 palabras que se factura en cada llamada.

### Solución 6: Agrupación de Ráfagas (*WhatsApp Message Debouncing*)
* En WhatsApp, una clienta suele mandar 3 mensajes seguidos en 4 segundos:
  1. *"Hola"*
  2. *"Soy Marta"*
  3. *"Quería saber si hoy a las 18 hay lugar"*
* Un *debouncer* espera 2 segundos cuando entra un mensaje; si entran 3 seguidos, los concatena en `"Hola\nSoy Marta\nQuería saber si hoy a las 18 hay lugar"` y hace **1 sola consulta a la IA en vez de 3** (**66% de ahorro** en usuarios que escriben cortado).

---

## 3. ¿Existen Skills, Plugins o Herramientas para esto?

### 1. En el Ecosistema de Antigravity / Marketplace:
* **Arize AX (`antigravity-plugins-partners/plugin/arize-skills`):** Es un plugin del Marketplace especializado en *Tracing, Evals & Prompt Optimization*. Permite auditar qué nodo de LangGraph consume más tokens en cada traza y optimizar los prompts.
* **Skill Interna de Arquitectura (`fireseed-methodology`):** Define la arquitectura de *Orquestación en Grafo con Fast-Path* y degradación elegante para no depender de llamadas redundantes al LLM.

### 2. Librerías Estándar en Python (que podemos aplicar directo en nuestro backend sin pagar servicios externos):
* **Filtro Dinámico de Tools en `direccion_agent.py`:** Se implementa en 30 líneas de Python puro dentro de nuestro propio nodo `agente_direccion_node`, seleccionando solo las 5–7 herramientas pertinentes según el mensaje de Deby.
* **Cortocircuito `return_direct` en `builder.py`:** En nuestro grafo de LangGraph, si el `ToolMessage` devuelto por una herramienta ya es una respuesta final formateada (comienza con `✦`, `✅`, `📊`, `📋`), el grafo termina directamente en `END` sin hacer la segunda llamada al LLM.

---

## 4. Comparativa de Costo Mensual Estimado (Estudio con ~50-80 Alumnas Activas)

| Escenario | Consumo por Mensaje (Dueña) | Consumo por Mensaje (Alumna) | Costo Mensual Estimado (USD) |
| :--- | :--- | :--- | :--- |
| **Estado en las pruebas (Sin optimizar)**<br>*(42 tools siempre + 2 llamadas + Todo en Gemini 3.8)* | ~26.000 tokens | ~4.500 tokens | **~$8.00 a $15.00 USD / mes** |
| **Con Optimización de Código**<br>*(Sub-Routing de 6 tools + Bypass 2da llamada + Fast-Path)* | **~2.800 tokens** (-89%) | **~1.200 tokens** (-73%) | **~$0.90 a $1.80 USD / mes** |
| **Con Optimización + Groq Gratis / Flash-Lite**<br>*(Texto en Groq/Lite y Fotos en Gemini Flash)* | **~2.800 tokens** (en Tier Gratis/Lite) | **~1.200 tokens** (en Tier Gratis/Lite) | **~$0.20 a $0.50 USD / mes** |

---

## 5. Plan de Acción Recomendado (Listo para Implementar)

Si estás de acuerdo, podemos aplicar **ahora mismo** en el código de Violett Pilates las **4 optimizaciones definitivas** para desplomar el consumo de tokens:

1. **Sub-Router de Herramientas en `direccion_agent.py`:** Para que cuando hable la dueña solo se envíen las 5–7 herramientas necesarias para esa consulta en vez de las 42 juntas (baja un **85%** los tokens de entrada).
2. **Bypass de 2da llamada en `builder.py`:** Para que cuando una herramienta ya devuelva el reporte o acción lista con formato WhatsApp, no vuelva a llamar al LLM gastando el doble.
3. **Prioridad a Modelos Lite (`gemini-2.5-flash-lite` / `gemini-2.0-flash-lite`) y Groq para texto:** Dejando los modelos grandes únicamente para lectura de fotos difíciles o razonamiento complejo.
4. **Fast-Path ampliado en `runner.py`:** Para que saludos, agradecimientos y consultas estáticas no consuman ni un solo token de API.
