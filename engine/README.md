# ⚡ FireSeed Engine — The Modular SaaS Framework
> **An enterprise-grade, plugin-driven core engine for subscription and appointment-based platforms.**  
> Built by **FireSeed** (*"Fueling Innovation"*).

[![Engine Architecture](https://img.shields.io/badge/Architecture-Microkernel_Plugin_System-blue.svg)](#-arquitectura-del-motor)
[![Methodology](https://img.shields.io/badge/Methodology-FireSeed_SOLID_%7C_Config--Driven-emerald.svg)](#-metodología-de-ingeniería)
[![Multi-Agent](https://img.shields.io/badge/Orchestration-LangGraph_DAG_%7C_Resilience_Cascade-purple.svg)](#-sistema-multi-agente-ia)
[![Quality](https://img.shields.io/badge/TypeScript-Strict_No_Any-orange.svg)](#-estándares-de-calidad)

---

## 🎯 ¿Qué es FireSeed Engine?

**FireSeed Engine** es un motor de software modular diseñado para crear aplicaciones SaaS multi-marca y multi-inquilino de alto rendimiento. En lugar de desarrollar cada proyecto desde cero o duplicar bases de código, el Engine actúa como una base universal donde cada caso de negocio se compone mediante **plugins ("piezas de Lego")** y se personaliza mediante **archivos de configuración desacoplados**.

### Propuesta de Valor Técnica
* **Cero Código Duplicado:** Un solo motor soporta múltiples verticales de negocio (ej. *Violett Pilates*, *Violett Estética*) sin necesidad de modificar el código fuente del núcleo.
* **Arquitectura de Plugins (Microkernel):** Los módulos de negocio se conectan, desconectan o actualizan de manera atómica sin riesgos de romper el resto del sistema.
* **Orquestación Multi-Agente con Estado (LangGraph):** Automatización conversacional con agentes especializados, memoria conversacional, Human-in-the-Loop y diagnóstico de fallos en segundo plano.
* **Escalabilidad Multi-Tenant:** Aislamiento seguro a nivel de contenedores Docker y esquemas relacionales PostgreSQL.

---

## 📐 Patrones Arquitectónicos y Nombres Formales

FireSeed Engine implementa estrictamente las mejores prácticas y patrones reconocidos en la ingeniería de software:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FIRESEED ENGINE CORE                            │
│  • Autenticación & Control de Acceso (RBAC)                            │
│  • Gestor Universal de Inquilinos (Config-Driven Loader)               │
│  • Enrutador Dinámico de Plugins & Inyector de Slots Visuales          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Contrato: PLUGIN_SPEC.md
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
 ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
 │    AGENDA    │            │  MEMBRESÍAS  │            │  ASISTENTE   │
 │   (Plugin)   │            │   (Plugin)   │            │ (LangGraph)  │
 └──────────────┘            └──────────────┘            └──────────────┘
```

### 1. Patrón Microkernel (Plugin Architecture)
El Engine se divide en dos partes:
* **Core Kernel:** Mantiene las responsabilidades comunes mínimas: inicialización, sesión de usuarios, despacho HTTP y carga de plugins.
* **Plugin Modules:** Residen en `engine/plugins/<nombre>/`. Cada plugin contiene de forma aislada su capa backend (modelos, migraciones, endpoints) y su capa frontend (vistas, rutas y componentes inyectables).

### 2. Arquitectura Dirigida por Configuración (*Config-Driven*)
El Engine separa rigurosamente la **lógica del motor** de la **configuración del cliente**:
* `config_<cliente>/client-config.json`: Define qué plugins se instancian en tiempo de ejecución (`active_plugins`), los tokens de estilo visual y los parámetros del negocio.
* `config_<cliente>/brand_persona.md`: Define la identidad de marca, tono de voz y protocolos de atención del asistente de IA.

### 3. Principios SOLID & Clean Architecture
* **S (Single Responsibility):** Desacoplamiento total entre componentes de interfaz (React), hooks de consumo de datos y servicios de dominio en Django (`services.py`).
* **O (Open/Closed):** El sistema está **abierto a extensión** (nuevos plugins) pero **cerrado a modificación** (el Core permanece inalterable).
* **L (Liskov Substitution):** Cualquier plugin que cumpla el contrato de exportación (`routes.tsx` y `urls.py`) puede ser reemplazado sin alterar el comportamiento global.
* **I (Interface Segregation):** Las herramientas y componentes solo consumen las interfaces mínimas necesarias.
* **D (Dependency Inversion):** El Core depende de interfaces abstractas de carga (`plugin_loader.py`), no de implementaciones concretas de plugins.

---

## 🧩 Anatomía de un Plugin ("Lego")

Cualquier módulo nuevo debe respetar la especificación [`PLUGIN_SPEC.md`](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/PLUGIN_SPEC.md):

```
engine/plugins/<nombre_plugin>/
├── backend/
│   ├── apps.py            # Registro de la app Django (name='plugins.<nombre>.backend')
│   ├── models.py          # Modelos de datos del plugin con restricciones estrictas
│   ├── views.py           # Endpoints del DRF (delgados, delegando en servicios)
│   ├── urls.py            # Rutas del backend inyectadas bajo /api/...
│   └── services.py        # Casos de uso y reglas de negocio puras
└── frontend/
    ├── components/        # Componentes atómicos de interfaz
    ├── hooks/             # Custom hooks para peticiones HTTP y estado local
    └── routes.tsx         # Contrato obligatorio de exportación para Vite
```

### Contrato Frontend (`routes.tsx`)
```typescript
import { RouteObject } from 'react-router-dom';

export const publicRoutes: RouteObject[] = [];
export const roleRoutes: Record<string, RouteObject[]> = {};
export const adminRoutes: RouteObject[] = [
  { path: 'mi-modulo', element: <MiModuloAdmin /> }
];
export const adminSidebarItems = [
  { name: 'Mi Módulo', path: '/admin/mi-modulo', icon: ModuloIcon }
];
export const slots = {
  'header-actions': <MiBotonInyectable />
};
```

---

## 🤖 Sistema Multi-Agente IA (LangGraph)

El plugin `asistente` implementa una arquitectura conversacional multi-agente basada en grafos con estado (`AgentState`):

```
                       [ Mensaje Entrante ]
                                │
                                ▼
                     ┌─────────────────────┐
                     │   ROUTER TRIAJE     │ (0ms Heurística / LLM)
                     └──────────┬──────────┘
                                │
         ┌──────────────┬───────┴───────┬──────────────┐
         ▼              ▼               ▼              ▼
   [ Recepción ]   [ Turnos ]      [ Finanzas ]   [ Dirección ] (Zero-Trust)
         │              │               │              │
         └──────────────┼───────────────┼──────────────┘
                        ▼               ▼
                 [ Tool Executor ] ──► (Aviso preliminar "Aguardame...")
                        │
                        ▼
                 [ Centinela Debugger ] ──► (Bitácora #ERR-xxxx en tiempo real)
```

### Características Técnicas del Asistente:
1. **Zero-Trust Security:** Solo la línea autorizada de la dirección (`DUENA`) tiene acceso a herramientas financieras y de gestión global.
2. **Human-in-the-Loop Fonético:** Búsqueda flexible tolerante a errores ortográficos y transcripción de audios mediante `SequenceMatcher`, con confirmación interactiva numerada.
3. **Espera Activa:** Subproceso paralelo en segundo plano que envía feedback instantáneo ante operaciones pesadas de base de datos.
4. **Cascada de Resiliencia (Fallback):**
   * Primario: **Google Gemini 2.5 Flash** (temperatura `0.1`, context window de 1M tokens).
   * Secundario: **Groq Cloud (Llama 3.3 70B)** o OpenAI GPT-4o mini.
   * Terciario: **Simulador Heurístico Local**, garantizando atención ininterrumpida ante caídas de proveedores externos.

---

## 🛡️ Estándares de Calidad y Convenciones

* **TypeScript Estricto:** Prohibido el uso de `any`. Toda entidad debe contar con su `interface` o `type` documentado.
* **Transacciones Atómicas:** Toda operación que afecte múltiples tablas de base de datos debe envolverse en `@transaction.atomic` para prevenir inconsistencias y *Race Conditions*.
* **Borrado Lógico (*Soft Delete*):** Registros críticos de usuarios, reservas y facturación no se destruyen con `DELETE`; se inactivan mediante `is_active = False` o marcas de tiempo.
* **Firma de Marca Obligatoria:**
  * En Python: `# Developed by FireSeed - Fueling Innovation`
  * En TypeScript: `/* Developed by FireSeed - Fueling Innovation */`
  * En UI: Leyenda sutil *"Powered by FireSeed"* en el pie de página de la aplicación.

---

## 🚢 Despliegue y Operación

El motor está contenerizado de fábrica con Docker y orquestado mediante `docker-compose.yml`. Las actualizaciones se aplican de forma atómica y sin caída de servicio a través del script [`deploy.sh`](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/deploy.sh):

```bash
# Despliegue en producción con actualización de Git, migraciones y limpieza de caché
./deploy.sh
```

---

## 📄 Autoría y Propiedad Intelectual

Desarrollado y mantenido por **FireSeed**.  
*“Fueling Innovation — Building Tomorrow's Software Architecture”*
