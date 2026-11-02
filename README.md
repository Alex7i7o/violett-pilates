# 🌸 Violett Pilates — Luxury Studio Operating System
> **An intelligent, automated management platform for high-end Pilates & Wellness studios.**  
> Powered by the **FireSeed Modular Engine** with Multi-Agent AI orchestration via **LangGraph & Google Gemini**.

[![Stack](https://img.shields.io/badge/Stack-React_19_%7C_Django_4.2_%7C_PostgreSQL_15-blue.svg)](#-stack-tecnológico)
[![AI Architecture](https://img.shields.io/badge/AI-LangGraph_%7C_Gemini_2.5_Flash_%7C_Multi--Agent-purple.svg)](#-oficina-virtual-ia-langgraph)
[![Architecture](https://img.shields.io/badge/Pattern-Microkernel_Plugins_%7C_Config--Driven-emerald.svg)](#-arquitectura-de-software)
[![DevOps](https://img.shields.io/badge/DevOps-Docker_Compose_%7C_Atomic_Deploy-orange.svg)](#-despliegue-y-devops)

---

## 🌟 Visión del Proyecto & Propuesta de Valor

**Violett Pilates** no es un software tradicional de reservas; es un **Sistema Operativo de Negocio Integral** diseñado para estudios de Pilates Reformer y centros de bienestar de alta gama. Combina una experiencia de usuario digital sobria y minimalista con una **Oficina Virtual Autónoma** que atiende a alumnas y asiste a la dirección 24/7 por WhatsApp.

### ¿Qué problemas resuelve?
* **Cero Fricción para Alumnas:** Reserva y cancelación autónoma de camillas Reformer en 2 clics, respetando políticas de cancelación anticipada (regla de 25 hs).
* **Oficina Virtual 24/7 en WhatsApp:** Un equipo de agentes de inteligencia artificial atiende consultas, inscribe alumnas, pasa alias bancarios y reporta turnos libres sin intervención humana.
* **Control Total para la Dirección (Deby):** Panel administrativo ejecutivo con métricas de ocupación, porcentaje de clases 100% llenas, conciliación automática de suscripciones y órdenes por voz/texto por WhatsApp con blindaje Zero-Trust.
* **Tolerancia a Fallos y Auditoría Transparente:** Monitoreo en tiempo real con un **Agente Centinela (Debugger)** que diagnostica incidentes técnicos y genera tickets de auditoría legibles para personas.

---

## 🏗️ Arquitectura de Software & Patrones de Ingeniería

El proyecto está construido sobre el **FireSeed Engine**, aplicando patrones formales de la ingeniería de software:

```
                                 [ Nginx Reverse Proxy ]
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
          [ Frontend (React 19) ]                         [ Backend (Django API) ]
          • Atomic Design Components                      • Clean Layered Architecture
          • Framer Motion (200-400ms)                     • PostgreSQL 15 (Atomic Tx)
          • Strict TypeScript (No any)                    • Celery / Tasks asíncronas
                    │                                               │
                    └───────────────────────┬───────────────────────┘
                                            ▼
                             [ Plugin: Asistente IA ]
                                            │
                          ┌─────────────────┴─────────────────┐
                          ▼                                   ▼
                [ Meta WhatsApp Cloud ]             [ LangGraph Engine ]
                • Webhooks con verificación         • Router de intención (0ms)
                • Audio transcription               • 5 Agentes Especialistas
                • Active Waiting ("Aguardame...")   • Coincidencia Fonética (HITL)
                                                    • Centinela Debugger (#ERR)
```

### 1. Patrón Microkernel (Arquitectura de Plugins / "Legos")
El núcleo del sistema (*Core*) proporciona la autenticación base, gestión de usuarios y enrutamiento dinámico. Las funcionalidades de negocio son módulos desacoplados ubicados en `engine/plugins/`:
* `agenda`: Grilla de horarios, camillas Reformer y control de asistencia.
* `membresias`: Abonos mensuales (4, 8, 12 clases), vigencias y créditos.
* `asistente`: Orquestación multi-agente con LangGraph, tools y debugger.
* `analitica`: Inteligencia de negocio, porcentaje de clases llenas y desglose contable.
* `comunicaciones`: Supervisión de WhatsApp en vivo y auditoría de correos transaccionales.

### 2. Arquitectura Dirigida por Configuración (*Config-Driven*)
El código del motor no posee nombres de clientes hardcodeados. Toda la identidad de marca, paleta cromática, reglas de negocio y plugins activos se configuran desde la carpeta [`config_pilates/`](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/config_pilates/):
* `client-config.json`: Lista de plugins activos y variables del cliente.
* `brand_persona.md`: Tono, voseo argentino y personalidad de la marca.
* `reglas_negocio.md`: Políticas de estudio, cupos por camilla y horarios.

### 3. Principios SOLID Aplicados
* **Single Responsibility (SRP):** Componentes visuales desacoplados de llamadas HTTP mediante custom hooks; agentes de IA acotados a su dominio.
* **Open/Closed (OCP):** El sistema se extiende creando carpetas en `engine/plugins/` sin alterar el Core.
* **Liskov Substitution (LSP):** Todo plugin cumple el contrato formal de exportación (`routes.tsx`).
* **Dependency Inversion (DIP):** El Core delega en abstracciones dinámicas (`plugin_loader`).

---

## 🤖 Oficina Virtual IA con LangGraph

El asistente virtual de WhatsApp no es un simple bot de respuestas enlatadas; es un **Grafo Multi-Agente con Estado**:

| Agente | Especialidad | Herramientas Clave |
| :--- | :--- | :--- |
| **🛎️ Recepcionista** | Bienvenida, contención humana, dudas sobre dolores de espalda y características de Pilates Reformer. | Asesoramiento empático en voseo argentino. |
| **📅 Turnos** | Consulta de vacantes en tiempo real por día/hora y reservas para alumnas. | `consultar_turnos_disponibles`, `reservar_turno_alumna`, `cancelar_turno_alumna`. |
| **💳 Finanzas** | Cotización de abonos, datos bancarios (Alias/CBU) y saldo de clases restantes. | `obtener_planes_y_precios`, `consultar_estado_abono_alumna`, `informar_datos_transferencia`. |
| **👑 Dirección (Deby)** | **Blindaje Zero-Trust:** Reportes mensuales de facturación, métricas de clases 100% llenas, altas/bajas de alumnas y aprobación de pagos. | `reporte_facturacion`, `obtener_reporte_ocupacion_mes`, `agendar_alumna_en_turno_duena`. |
| **🛡️ Centinela Debugger** | Captura silenciosa de excepciones técnicas, cuotas de API y errores ORM. Genera diagnósticos humanos y tickets auditables (`#ERR-xxxx`). | `RegistroErrorIA`, bitácora en panel web. |

### Características Avanzadas de Interacción:
* **Espera Activa:** Ante consultas pesadas de base de datos, envía un aviso preliminar (*"✦ Aguardame un segundito que ya te preparo la información..."*) para erradicar la sensación de demora.
* **Human-in-the-Loop Fonético:** Tolera audios y nombres con faltas de ortografía (*"marzuk"* $\to$ *Laila Marzzuck*), solicitando confirmación con opciones numeradas antes de alterar la agenda.
* **Cascada de Resiliencia:** Prioridad en **Google Gemini 2.5 Flash** (temperatura `0.1` anti-alucinaciones) con conmutación automática ante fallos a **Groq (Llama 3.3 70B)**, OpenAI y Simulador Heurístico Local.

---

## 📊 Dashboard de Inteligencia de Negocio

El módulo de Analítica ([`AnalyticsDashboard.tsx`](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/plugins/analitica/frontend/views/AnalyticsDashboard.tsx)) ofrece métricas en tiempo real:
* **% de Clases 100% Llenas:** Ratio de turnos del mes que completaron todas sus camillas sin cupos ociosos.
* **Ocupación Promedio de Camillas:** Promedio ponderado de camillas ocupadas por clase.
* **Dinámica Operativa:** Conteo de clases dictadas, llenas y canceladas.
* **Tiempo Administrativo Ahorrado:** Horas de trabajo humano automatizadas por el sistema (reservas, cancelaciones y recordatorios).
* **Desglose Contable Interactivo:** Auditoría de facturación, planes vendidos y estados de cobro por alumna con ordenamiento y filtros instantáneos.

---

## 🛠️ Stack Tecnológico

```
Frontend:           React 19, TypeScript, Vite, Tailwind CSS, Framer Motion, Lucide Icons, Sonner
Backend:            Python 3.12, Django 4.2+, Django REST Framework, Psycopg2
Database:           PostgreSQL 15 (Relational, Strict Integrity Constraints)
AI Orchestration:   LangGraph, LangChain Core, Google Gemini 2.5/2.0 Flash, Groq Cloud
Infrastructure:     Docker, Docker Compose, Nginx Reverse Proxy, Ubuntu Linux VPS
Testing & Quality:  E2E testing suites, makemigrations isolation, strict typing
```

---

## 🚀 Despliegue y Puesta en Marcha

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Alex7i7o/violett-pilates.git
cd violett-pilates
```

### 2. Configurar Variables de Entorno
Crear el archivo `.env` basado en `.env.example`:
```env
SECRET_KEY=tu_clave_secreta_super_segura
DEBUG=False
ALLOWED_HOSTS=violett.com.ar,www.violett.com.ar,localhost

# Base de Datos
POSTGRES_DB=violett_pilates
POSTGRES_USER=violett_user
POSTGRES_PASSWORD=tu_password_seguro

# Inteligencia Artificial
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_VERIFY_TOKEN=...

# Correo Transaccional (Resend)
EMAIL_HOST_PASSWORD=re_...
```

### 3. Despliegue con un solo comando ([`deploy.sh`](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/deploy.sh))
El script se encarga de descargar cambios de Git, compilar contenedores, aplicar migraciones y limpiar caché de Docker:
```bash
chmod +x deploy.sh
./deploy.sh
```

*(Opcional para inicializar datos de prueba en un nuevo entorno: `./deploy.sh --seed`)*

---

## 📜 Licencia y Autoría

Desarrollado con pasión e innovación por **FireSeed**.  
*“Fueling Innovation — Crafting High-Performance Modular Software”*

* Todos los derechos reservados © 2026 FireSeed & Violett Pilates.
