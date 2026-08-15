# Documento de Especificación de Requerimientos del Sistema (SRS)
## Aplicación Web de Reservas y Gestión para Estudio de Pilates

---

## 1. Visión General del Proyecto
El objetivo del proyecto es el desarrollo de una plataforma web autogestionable de reservas y administración de clases de Pilates. El sistema busca automatizar la programación de turnos, el control estricto de cupos por clase, el ciclo de vida de los planes de alumnos y las comunicaciones/notificaciones, garantizando máxima autonomía para los clientes y flexibilidad total de configuración para la administración del estudio.

---

## 2. Parámetros Globales Configurables (Panel de Administración)
Todos los valores del sistema deben ser parametrizables desde un panel de control exclusivo para el dueño o administrador, de modo que puedan modificarse dinámicamente sin alterar la arquitectura de código ni requerir intervención técnica futura.

* **Capacidad Máxima por Clase:** Valor por defecto: `3 alumnos`.
* **Capacidad Mínima por Clase:** Valor por defecto: `2 alumnos`.
* **Ventana Límite de Modificación/Cancelación por Cliente:** Valor por defecto: `24 horas` antes del inicio del turno.
* **Umbral de Evaluación Automática de Clase (Cierre/Alerta):** Valor por defecto: `25 horas` antes del inicio del turno.
* **Vencimiento de Planes de Clases:** Valor por defecto: `30 días corridos`.
* **Alerta Preventiva de Vencimiento de Plan:** Valor por defecto: `5 días` antes de la expiración.

---

## 3. Módulo de Autenticación y Gestión de Usuarios

### 3.1 Registro y Métodos de Acceso
* **Login Social (OAuth 2.0):** Autenticación rápida e integrada mediante **Google Sign-In**.
* **Registro Convencional:** Opción de registro/login mediante correo electrónico y contraseña.
* **Roles de Usuario:**
  * **Cliente / Alumno:** Acceso restringido a la interfaz de usuario.
  * **Administrador / Dueño:** Acceso completo al backoffice de gestión, configuración global y agenda.

### 3.2 Panel de Control del Cliente (Dashboard)
El usuario dispone de una vista privada donde visualiza:
* **Estado del Plan Activo:** Tipo de plan, fecha exacta de vencimiento y saldo de clases restantes.
* **Próximas Clases:** Listado detallado de turnos agendados futuros (día, hora y modalidad).
* **Historial de Asistencia:** Registro de clases ya tomadas/completadas.
* **Acciones Rápidas:** Opciones para agendar nuevos turnos, modificar/cancelar reservas existentes o renovar la suscripción.

---

## 4. Módulo de Agenda, Horarios y Lógica de Recurrencia

### 4.1 Gestión Dinámica de Agenda (Backoffice)
* **Programación Semanal Recurrente:** Creación de plantillas de clases que se repiten automáticamente semana a semana.
* **Gestión de Horarios Salteados / Dinámicos:** Capacidad de crear, editar o eliminar bloques de hora específicos e irregulares en días puntuales (por ejemplo, habilitar una clase única a las 10:00, 12:00, 15:00 o 20:00) sin romper la plantilla base.

### 4.2 Lógica de Asignación y Recurrencia de Horarios (Asignación de Cupo Reservado)
* **Turno Puntual:** El cliente se anota para una fecha y hora específica.
* **Recurrencia Semanal con Bloqueo de Cupo:**
  * Si el cliente selecciona la opción de asistir de forma recurrente (ejemplo: *Martes a las 13:00 hs*), **el cupo de ese día y hora queda bloqueado permanentemente a su nombre**.
  * **Protección contra despojo de lugar:** La reserva del horario semanal se mantiene reservada para ese cliente incluso entre transiciones de planes. El lugar solo se libera y queda disponible para terceros si el cliente **no renueva su plan** al momento del vencimiento.
* **Cancelación de Clase Recurrente:**
  * Al intentar cancelar o modificar un turno que forma parte de una regla recurrente, el sistema despliega una confirmación interactiva preguntando:
    1. *¿Deseas cancelar únicamente la clase de esta semana?*
    2. *¿Deseas cancelar esta clase y todas las sesiones futuras asignadas?*

---

## 5. Motor de Reservas, Reglas de Negocio y Cancelaciones

### 5.1 Regla de Autogestión y Cancelación (24 Horas)
* **Modificación/Cancelación Permitida:** Si faltan **más de 24 horas** para el inicio de la clase, el cliente puede cancelar o reagendar libremente. La clase se acredita de inmediato a su saldo.
* **Cancelación Tardía:** Si faltan **menos de 24 horas**, el sistema bloquea la opción de cancelación/modificación por parte del cliente o la marca como consumida sin restitución de crédito.

### 5.2 Consumo de Clases
* Cuando la fecha y hora de la clase transcurren, el sistema descuenta automáticamente la clase del saldo del plan del cliente y la registra en el historial como "Tomada".

---

## 6. Automatizaciones del Sistema (Cron Jobs) y Evaluación a las 25 Horas

Exactamente a las **25 horas previas** al inicio de cada clase programada, el motor del backend ejecuta una verificación automatizada según el nivel de ocupación:

```
[ Evaluador de Estado de Clase (a las 25hs del inicio) ]
       │
       ├─► ¿Inscriptos < Mínimo (2 personas)? 
       │     └─► ACCIÓN: Cancelar clase automáticamente.
       │                 Devolver crédito/cupo a los afectados.
       │                 Notificar cancelación al alumno vía WhatsApp/Push.
       │
       ├─► ¿Inscriptos == Mínimo (2 de 3 personas)? 
       │     └─► ACCIÓN: Habilitar alerta de cupo disponible.
       │                 Enviar notificación masiva a usuarios web sobre la vacante.
       │
       └─► ¿Inscriptos >= Mínimo (2 o 3 personas)? 
             └─► ACCIÓN: Mantener clase activa.
                         Enviar recordatorio de asistencia a los inscriptos.
```

1. **Escenario A: Inscriptos < Capacidad Mínima (Ej. 0 o 1 alumno)**
   * La clase se **cancela y cierra automáticamente**. Ya no se admiten nuevas reservas para ese bloque.
   * Se restituye el crédito/cupo al alumno inscripto.
   * Se envía una notificación inmediata al alumno informando la cancelación del turno por no alcanzar el mínimo requerido.
2. **Escenario B: Inscriptos == Capacidad Mínima (Ej. 2 de 3 alumnos)**
   * La clase se confirma.
   * Se genera una **alerta de vacante disponible** que se envía como notificación a los clientes activos informando que hay 1 cupo libre para ese horario.
3. **Escenario C: Inscriptos >= Capacidad Mínima (Ej. 2 o 3 alumnos)**
   * Se envía un **recordatorio automatizado de asistencia** a todos los alumnos inscriptos.

---

## 7. Sistema de Notificaciones, Alertas y Bot de WhatsApp

El sistema contará con una arquitectura multicanal de notificaciones: **Web Push Notifications** para usuarios dentro de la plataforma y una integración con **WhatsApp API** coordinada por un Agente Bot con personalidad corporativa personalizada para el estudio.

### 7.1 Bot de WhatsApp Inteligente (Agente / Gem)
* **Personalidad e Identidad de Marca:** El bot operará como un asistente virtual del estudio de Pilates, utilizando un tono cercano, servicial y profesional.
* **Integración con Eventos:** Se conecta mediante webhooks con el sistema central para redactar e interactuar de forma humanizada.

### 7.2 Eventos y Disparadores de Notificaciones

| Evento / Condición | Disparador (Trigger) | Canal | Mensaje / Acción |
| :--- | :--- | :--- | :--- |
| **Cancelación Automática de Clase** | 25 hs antes (si hay < 2 personas) | WhatsApp + Push | Notificación del Bot informando que la clase fue cancelada y el turno fue devuelto a su saldo. |
| **Alerta de Cupo Libre** | 25 hs antes (si hay exactamente 2 personas) | Web Push + WhatsApp | Difusión de oportunidad: *"¡Queda 1 lugar libre para la clase de mañana a las X hs! Entra a reservar."* |
| **Recordatorio de Asistencia** | 25 hs antes de la clase | WhatsApp + Push | Mensaje del Bot recordando el turno del día siguiente. |
| **Última Clase del Plan** | Queda 1 sola clase en el saldo | WhatsApp + Push | Alerta preventiva para incentivar la renovación del plan. |
| **Alerta de Vencimiento Próximo** | 5 días antes del vencimiento (con clases pendientes) | WhatsApp + Push | Advertencia: *"Te quedan 5 días para usar tus clases restantes antes de que venza el plan."* |
| **Alerta de Pérdida de Horario Recurrente** | Vencimiento del plan sin renovación | WhatsApp | Aviso de que su cupo fijo semanal ha sido liberado para otros alumnos. |

---

## 8. Consideraciones de Arquitectura y Escalabilidad
* **Independencia de Parámetros:** Toda la lógica de negocio (cupos, horas de tolerancia, días de vencimiento) se consulta directamente desde la tabla de configuración global antes de ejecutar cualquier acción.
* **Persistencia de Horarios Recurrentes:** La tabla de mapeo de recurrencia une la relación `Usuario <-> Día/Hora` con un estado prioritario sobre el calendario de inscripciones generales, liberándose únicamente ante un evento explicito de baja de plan o cancelación manual.
