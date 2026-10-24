# ✦ Guía Maestra de Mensajería WhatsApp, Plantillas y Costos Mensuales
### Violett Pilates Reformer • Sistema Asistente Multi-Agente & CRM

---

## 1. Resumen de Casos de Uso y Destinatarios

El sistema de mensajería de **Violett Pilates** contempla 4 grandes audiencias y 18 escenarios de comunicación automatizada:

```
                                  ┌───► 1. Alumnas / Clientes (Turnos, Recordatorios, Pagos)
                                  ├───► 2. Reactivación & Ofertas (Volver al Lugar, Camillas Libres)
✦ MOTOR DE MENSAJERÍA WHATSAPP ──┼───► 3. Profesoras (Cronograma Diario, Reemplazos, Bajas)
                                  └───► 4. Dueña / Administración (Alertas VIP, Comprobantes, Fusión)
```

---

## 2. Catálogo Oficial de Plantillas para Meta WhatsApp Cloud API

> [!IMPORTANT]
> **Regla de Oro de Meta (WhatsApp Business Cloud API):**
> - Los mensajes de texto libre solo pueden enviarse dentro de una **ventana de 24 horas** abierta por la clienta al escribirnos.
> - Cualquier mensaje enviado por el sistema de forma proactiva fuera de esa ventana (recordatorios, avisos nocturnos, promociones, reactivaciones) **debe usar una plantilla pre-aprobada por Meta**.
> - En Meta existen 3 categorías principales:
>   - **UTILITY (Utilidad):** Mensajes transaccionales y operativos (confirmaciones de turnos, recordatorios, avisos de cuenta). Tienen aprobación inmediata (minutos) y tarifa económica.
>   - **MARKETING:** Ofertas, promociones, campañas de volver al lugar, invitaciones y novedades.
>   - **AUTHENTICATION:** Códigos de un solo uso (OTP) para verificar identidad.

---

### Grupo A: Alumnas y Clientes (Operativas / Transaccionales)

#### 1. `reserva_confirmada` (Categoría: `UTILITY`)
- **Disparador:** La alumna reserva un turno (por la web o por el bot).
- **Variables:** `{{1}}` Nombre | `{{2}}` Clase | `{{3}}` Día y Fecha | `{{4}}` Horario
- **Texto:**
  > ¡Hola {{1}}! ✦ Tu lugar en Reformer está confirmado.
  > 
  > 📅 **Clase:** {{2}}
  > 🗓️ **Fecha:** {{3}}
  > ⏰ **Horario:** {{4}} hs
  > 📍 **Estudio:** Gral. Guido 1573, Ramos Mejía.
  > 
  > Te sugerimos llegar 5 minutos antes para prepararte y arrancar relajada ✨.
- **Botones rápidos (Quick Reply):** `[ Ver mis turnos ]` `[ Cancelar turno ]`

---

#### 2. `recordatorio_clase_proactivo` (Categoría: `UTILITY`)
- **Disparador:** 2 a 3 horas antes del inicio de la clase (cron automático).
- **Variables:** `{{1}}` Nombre | `{{2}}` Clase | `{{3}}` Horario | `{{4}}` Profesora
- **Texto:**
  > ¡Hola {{1}}! ✦ Te recordamos que hoy tenés tu clase de {{2}} a las {{3}} hs con la profe {{4}} ✨.
  > 
  > Te esperamos en nuestro espacio boutique de Ramos Mejía (Gral. Guido 1573). ¡Traé ropa cómoda y muchas ganas de reconectar con tu cuerpo! ✦
- **Botones rápidos:** `[ Confirmar asistencia ]` `[ Cancelar / Reprogramar ]`

---

#### 3. `reserva_cancelada_alumna` (Categoría: `UTILITY`)
- **Disparador:** La alumna cancela su turno desde la app o por chat.
- **Variables:** `{{1}}` Nombre | `{{2}}` Clase y Fecha | `{{3}}` Estado del crédito
- **Texto:**
  > Hola {{1}} ✦ Tu cancelación para la clase de {{2}} fue procesada con éxito.
  > 
  > {{3}}
  > 
  > Podés reprogramar cuando gustes directamente desde la app o escribiéndonos por acá. ¡Que tengas lindo día!
- *(Nota: Si canceló con más de 6 hs de anticipación, `{{3}}` dice: "Tu crédito fue reintegrado a tu abono para que lo uses en otra clase ✨". Si fue tardía, explica la política del estudio).*

---

#### 4. `clase_cancelada_bajo_cupo` (Categoría: `UTILITY`)
- **Disparador:** El sistema detecta que hay menos de 2 alumnas inscriptas a 24 hs de la clase (regla de cupo mínimo de Violett).
- **Variables:** `{{1}}` Nombre | `{{2}}` Clase | `{{3}}` Día y Horario
- **Texto:**
  > ¡Hola {{1}}! ✦ Te escribimos desde Violett Pilates.
  > 
  > Te contamos que para el turno de {{2}} del {{3}} no se alcanzó el cupo mínimo requerido para dictar la clase (mínimo 2 alumnas).
  > 
  > Por este motivo, la clase fue cancelada y tu crédito ya fue reintegrado automáticamente a tu abono ✦. Tenés tu clase lista para reprogramar en el horario que más cómodo te quede.
  > 
  > ¿Te gustaría que te pasemos los horarios disponibles para reubicarte? ✨
- **Botones rápidos:** `[ Ver horarios libres ]` `[ Hablar con Débora ]`

---

#### 5. `comprobante_pago_recibido` (Categoría: `UTILITY`)
- **Disparador:** La clienta envía una foto/PDF de transferencia por WhatsApp.
- **Variables:** `{{1}}` Nombre | `{{2}}` Monto detectado | `{{3}}` ID de referencia
- **Texto:**
  > ¡Muchas gracias {{1}}! ✦ Recibimos tu comprobante de pago por ${{2}} (Ref: #{{3}}).
  > 
  > Nuestro equipo ya lo está verificando. Apenas quede acreditado en la cuenta te confirmamos y te activamos el abono de inmediato ✨.

---

#### 6. `abono_activado_confirmacion` (Categoría: `UTILITY`)
- **Disparador:** La dueña aprueba el pago en el panel o desde el chat de WhatsApp.
- **Variables:** `{{1}}` Nombre | `{{2}}` Nombre del Plan | `{{3}}` Cantidad de Clases | `{{4}}` Fecha de Vencimiento
- **Texto:**
  > ¡Pago confirmado {{1}}! 🎉✦
  > 
  > Tu abono **{{2}}** ya está activo:
  > • Créditos disponibles: **{{3}} clases**
  > • Vigencia hasta el: **{{4}}**
  > 
  > Ya podés ingresar a tu cuenta para agendar tus clases en las 3 camillas Reformer o pedirnos los turnos por acá. ¡Bienvenida a tu práctica! ✨
- **Botones rápidos:** `[ Agendar mi primer clase ]`

---

#### 7. `alerta_vencimiento_abono` (Categoría: `UTILITY`)
- **Disparador:** Faltan 4 días para que venza el abono o le queda solo 1 clase disponible.
- **Variables:** `{{1}}` Nombre | `{{2}}` Clases restantes | `{{3}}` Fecha de vencimiento
- **Texto:**
  > ¡Hola {{1}}! ✦ Queremos avisarte que te queda(n) **{{2}}** en tu plan actual, con vencimiento el **{{3}}**.
  > 
  > Si querés conservar tus días y horarios fijos para el próximo mes, podés renovar tu abono hoy mismo y asegurarte tu camilla ✨.
- **Botones rápidos:** `[ Renovar abono ]` `[ Ver planes disponibles ]`

---

### Grupo B: Reactivación, Ofertas & Retención (Marketing)

#### 8. `camillas_libres_proactivo` (Categoría: `MARKETING`)
- **Disparador:** Se liberaron camillas en turnos próximos (próximas 24-48h) y el asistente le ofrece a alumnas con créditos activos para completar las 3 camillas (respetando si tienen parejas inseparables como madre e hija).
- **Variables:** `{{1}}` Nombre | `{{2}}` Día y Fecha | `{{3}}` Horario | `{{4}}` Clase
- **Texto:**
  > ¡Hola {{1}}! ✦ Se liberó una camilla en Reformer para el {{2}} a las {{3}} hs en {{4}}.
  > 
  > Como tenés créditos disponibles en tu abono, te reservamos la prioridad por si tenés ganas de sumar una práctica extra esta semana ✨.
  > 
  > ¿Te gustaría que te reservemos el lugar?
- **Botones rápidos:** `[ ¡Sí, anótame! ]` `[ En otro momento ]`

---

#### 9. `reactivacion_volver_al_lugar` (Categoría: `MARKETING`)
- **Disparador:** Alumnas que no asisten ni tienen abono activo hace más de 30 o 45 días ("Win-back").
- **Variables:** `{{1}}` Nombre | `{{2}}` Beneficio / Descuento exclusivo | `{{3}}` Vigencia de la oferta
- **Texto:**
  > ¡Hola {{1}}! ✦ Te extrañamos mucho en Violett.
  > 
  > Sabemos que a veces la rutina se complica, pero tu cuerpo merece ese momento de reconexión y fuerza que solo el Reformer te da ✨.
  > 
  > Para que vuelvas a tu práctica, te guardamos un **{{2}}** en tu próximo abono renovando antes del {{3}}.
  > 
  > ¿Te gustaría que te contemos los horarios disponibles para esta semana?
- **Botones rápidos:** `[ Quiero volver con descuento ]` `[ No por ahora ]`

---

#### 10. `onboarding_bienvenida_prospecto` (Categoría: `MARKETING`)
- **Disparador:** Una persona consulta por primera vez o la dueña carga su número desde la lista de interesadas.
- **Variables:** `{{1}}` Nombre o Saludo
- **Texto:**
  > ¡Hola{{1}}! ✦ Te damos la bienvenida a **Violett Pilates Boutique**.
  > 
  > Nuestro espacio en Ramos Mejía está diseñado para brindarte una experiencia íntima y personalizada:
  > • Máximo 3 camillas Reformer por turno.
  > • Sesiones de 60 minutos (55 min de práctica + 5 min de descompresión asistida).
  > • Corrección postural milimétrica.
  > 
  > ¿Te gustaría conocer nuestros abonos mensuales o reservar una clase de prueba? ✨
- **Botones rápidos:** `[ Ver Abonos y Precios ]` `[ Horarios de Prueba ]` `[ Hablar con Débora ]`

---

#### 11. `promo_especial_estudio` (Categoría: `MARKETING`)
- **Disparador:** Campañas masivas del estudio (Día de la Madre, Promo Primavera, Black Friday, Apertura de nuevos turnos).
- **Variables:** `{{1}}` Nombre | `{{2}}` Título de la Promo | `{{3}}` Detalle del beneficio | `{{4}}` Código o Enlace
- **Texto:**
  > ¡Hola {{1}}! ✦ Tenemos una novedad especial para vos:
  > 
  > 🌟 **{{2}}**
  > {{3}}
  > 
  > Los cupos en camillas son súper limitados (solo 3 por horario) y la promo es válida hasta agotar disponibilidad.
  > 
  > ¿Querés asegurar tu lugar ahora? ✨
- **Botones rápidos:** `[ Aprovechar promo ]` `[ Más info ]` `[ Detener avisos ]`

---

### Grupo C: Profesoras y Staff Docente (Operativo)

#### 12. `agenda_docente_diaria` (Categoría: `UTILITY`)
- **Disparador:** Todas las noches a las 20:30 hs enviando el cronograma del día siguiente.
- **Variables:** `{{1}}` Nombre de la Profe | `{{2}}` Día y Fecha | `{{3}}` Lista de turnos y alumnas
- **Texto:**
  > ¡Hola {{1}}! ✦ Te compartimos tu cronograma de clases en Violett Pilates para mañana **{{2}}**:
  > 
  > {{3}}
  > 
  > Recordá llegar 10 minutos antes para ventilar y preparar las camillas. ¡Que tengas una excelente jornada! ✨
- **Botones rápidos:** `[ Recibido / Confirmado ]`

---

#### 13. `aviso_profe_clase_cancelada` (Categoría: `UTILITY`)
- **Disparador:** Un turno se cancela a menos de 24 hs por bajo cupo o sin alumnas (evita que la profe viaje en vano).
- **Variables:** `{{1}}` Nombre de la Profe | `{{2}}` Clase | `{{3}}` Día y Horario | `{{4}}` Motivo
- **Texto:**
  > ¡Hola {{1}}! ✦ Te avisamos que el turno de {{2}} del {{3}} fue cancelado automáticamente al {{4}}.
  > 
  > No hace falta que asistas en ese horario. ¡Que disfrutes tu descanso! ✨

---

#### 14. `solicitud_reemplazo_docente` (Categoría: `UTILITY`)
- **Disparador:** La dueña o el sistema buscan suplente ante ausencia de una profesora.
- **Variables:** `{{1}}` Nombre de la Profe | `{{2}}` Profe a cubrir | `{{3}}` Día y Fecha | `{{4}}` Horario
- **Texto:**
  > ¡Hola {{1}}! ✦ Necesitamos cubrir una clase de Violett:
  > • Titular: Profe {{2}}
  > • Fecha: {{3}}
  > • Horario: {{4}} hs (Reformer - 3 camillas)
  > 
  > ¿Tenés disponibilidad para cubrir este turno? ✨
- **Botones rápidos:** `[ Sí, puedo cubrir ]` `[ No tengo disponibilidad ]`

---

#### 15. `confirmacion_reemplazo_asignado` (Categoría: `UTILITY`)
- **Disparador:** Una profesora acepta el reemplazo y queda guardada en el sistema.
- **Variables:** `{{1}}` Nombre de la Profe | `{{2}}` Clase y Fecha | `{{3}}` Horario
- **Texto:**
  > ¡Excelente {{1}}! ✦ Quedaste confirmada como profesora a cargo de {{2}} a las {{3}} hs.
  > 
  > Ya figura actualizado en la agenda del estudio. ¡Muchas gracias por tu compromiso! ✨

---

### Grupo D: Dueña del Estudio (Supervisión VIP & Human-in-the-Loop)

#### 16. `alerta_duena_comprobante` (Categoría: `UTILITY`)
- **Disparador:** Una clienta envía comprobante de pago por WhatsApp y la visión IA extrae los datos bancarios.
- **Variables:** `{{1}}` Nombre Alumna | `{{2}}` Monto | `{{3}}` Banco / Operación | `{{4}}` ID de Aprobación
- **Texto:**
  > ✦ **NUEVO COMPROBANTE PARA VALIDAR** ✦
  > 
  > • Alumna: {{1}}
  > • Monto: ${{2}}
  > • Banco / Transf: {{3}}
  > • ID: #{{4}}
  > 
  > ¿Aprobás la activación del abono?
- **Botones rápidos:** `[ Aprobar #{{4}} ]` `[ Rechazar ]` `[ Ver en CRM ]`

---

#### 17. `alerta_duena_clase_critica` (Categoría: `UTILITY`)
- **Disparador:** El optimizador detecta clases con 1 sola alumna a 30 hs del turno y sugiere fusión para ahorrar horas de pago docente.
- **Variables:** `{{1}}` Día y Horario | `{{2}}` Alumna inscripta | `{{3}}` Opción de fusión recomendada
- **Texto:**
  > ✦ **OPORTUNIDAD DE OPTIMIZACIÓN EN AGENDA** ✦
  > 
  > El turno del {{1}} tiene solo 1 alumna ({{2}}).
  > Recomendación IA: {{3}}.
  > 
  > ¿Querés que el asistente le ofrezca reubicarse o mantenemos la clase?

---

#### 18. `alerta_duena_consulta_humana` (Categoría: `UTILITY`)
- **Disparador:** La clienta plantea un tema médico complejo, una queja o solicita expresamente hablar con Débora.
- **Variables:** `{{1}}` Nombre Alumna | `{{2}}` Teléfono | `{{3}}` Resumen de la consulta
- **Texto:**
  > ✦ **CONSULTA DE ALUMNA DERIVADA A DÉBORA** ✦
  > 
  > • Alumna: {{1}} ({{2}})
  > • Motivo: "{{3}}"
  > 
  > El bot ha pausado sus respuestas automáticas para este contacto para que puedas responderle desde tu WhatsApp sin interferencias.

---

## 3. Estructura de Precios Oficial de Meta (Cloud API)

A partir de 2024 / 2025, Meta factura en dólares (USD) según el **tipo de conversación de 24 horas** y el país del destinatario (tarifas para Argentina / Rest of Latin America):

| Categoría | Costo aprox. por conversación (24 hs) | Quién lo inicia | Ejemplos en Violett |
| :--- | :--- | :--- | :--- |
| **Service (Atención al Cliente)** | **GRATIS (primeras 1.000 / mes)** <br>Luego ~$0.015 USD | Alumna / Clienta | Alumna pregunta precios, consulta si hay lugar mañana, pide cambiar turno. |
| **Utility (Utilidad)** | **~$0.0125 - $0.0150 USD** | El Sistema (Violett) | Recordatorio de clase, confirmación de reserva, aviso de bajo cupo, agenda a profes, alertas a Débora. |
| **Marketing** | **~$0.0550 - $0.0620 USD** | El Sistema (Violett) | Promo de temporada, "volver al lugar", oferta de camillas libres, bienvenida a prospectos. |
| **Authentication** | **~$0.0315 USD** | El Sistema (Violett) | Códigos OTP de seguridad (si se usaran en lugar de email). |

> [!TIP]
> **Beneficio Clave:** Meta otorga a cada cuenta comercial de WhatsApp (WABA) **1.000 conversaciones de SERVICIO GRATIS todos los meses**.
> Dado que una clienta suele iniciar la conversación para consultar o pedir un turno, todas esas charlas de atención al cliente con la IA **tienen costo $0.00**.

---

## 4. Presupuesto Mensual Estimado para Violett Pilates

Considerando la capacidad real del estudio:
- **Infraestructura:** 3 Camillas Reformer.
- **Volumen:** ~35 a 45 turnos semanales = ~160 a 180 clases por mes.
- **Base activa:** ~70 a 110 alumnas registradas.

### Escenario A: Operación Estándar Mensual

| Concepto | Mensajes / Conversaciones | Tarifa Unitaria | Costo Total USD |
| :--- | :--- | :--- | :--- |
| **Recordatorios proactivos de clase** (Utility) | ~350 conversaciones | $0.014 USD | **$4.90 USD** |
| **Confirmaciones de reserva y cancelaciones** (Utility) | ~120 conversaciones | $0.014 USD | **$1.68 USD** |
| **Avisos nocturnos a profesoras** (Utility) | ~30 envíos | $0.014 USD | **$0.42 USD** |
| **Alertas a la dueña (comprobantes y reportes)** (Utility) | ~40 envíos | $0.014 USD | **$0.56 USD** |
| **Consultas entrantes de alumnas y prospectos** (Service) | ~300 conversaciones | **$0.00 USD** *(Incluidas en las 1.000 gratis)* | **$0.00 USD** |
| **Llenado proactivo de camillas libres** (Marketing) | ~40 contactos | $0.058 USD | **$2.32 USD** |
| **Reactivación mensual "Volver al lugar"** (Marketing) | ~50 alumnas inactivas | $0.058 USD | **$2.90 USD** |
| **SUBTOTAL MENSUAL META:** | | | **~$12.78 USD** |

> [!NOTE]
> **Costo Total Mensual:** Aprox. **$12 a $15 USD por mes** (alrededor de **$15.000 a $19.000 ARS**).
> Equivale a **menos de la mitad de una sola cuota de un abono de 8 clases**, y cubre la automatización completa del 100% de los turnos, cobros y retención del estudio.

---

## 5. Comparativa: Meta Cloud API vs. Evolution API (QR Celular)

| Criterio | Meta WhatsApp Cloud API (Oficial) | Evolution API / QR (Emulador WhatsApp Web) |
| :--- | :--- | :--- |
| **Costo por mensaje** | ~$0.014 a $0.058 USD por conversación. | **$0.00 USD** (Ilimitado y gratuito). |
| **Estabilidad de conexión** | **100% permanente**. En la nube de Meta; nunca se desconecta ni depende de que un teléfono esté prendido o con batería. | Depende de la sesión de WhatsApp Web; si se cierra la sesión en el celular o Meta detecta actividad no humana, hay que re-escanear el QR. |
| **Riesgo de bloqueo o baneo** | **Cero**. Está homologado oficialmente por Meta Business. | **Medio / Alto** si se mandan promociones a personas que no tienen el número agendado. |
| **Aprobación de plantillas** | Requiere crear plantillas en Meta Business Manager. | No requiere plantillas; envía cualquier texto o imagen libremente. |
| **Botones interactivos** | Soporta botones nativos rápidos (Quick Replies) y menús desplegables oficiales. | Soporte parcial (a veces los botones no se muestran en iPhone). |
| **Recomendación para Violett** | **Recomendado para el Asistente Oficial** por confiabilidad, imagen de marca boutique y evitar riesgos de perder la línea comercial. | Ideal como respaldo secundario o para desarrollos internos. |

---

## 6. Guía Paso a Paso: Cómo Enviar una Promoción Masiva a Todos los Contactos

Cuando quieras lanzar una promoción para fechas especiales (ej: Día de la Madre, Descuentos de Primavera, 2x1 en primera clase, etc.), el procedimiento consta de 4 pasos:

### Paso 1: Crear y Aprobar la Plantilla de Marketing en Meta
1. Ingresás al panel de **Meta Business Manager** (business.facebook.com) $\rightarrow$ *Administrador de WhatsApp* $\rightarrow$ *Plantillas de mensajes*.
2. Tocás en **Crear Plantilla**:
   - Nombre: `promo_primavera_violett` (en minúsculas, sin espacios).
   - Categoría: **Marketing**.
   - Idioma: **Español (Argentina)** o **Español**.
3. Redactás el texto con variables dinámicas:
   > ¡Hola {{1}}! ✦ En Violett Pilates queremos celebrar la llegada de la primavera con vos 🌸.
   > 
   > Durante esta semana tenés un **{{2}}** en todos nuestros abonos de Reformer. 
   > Recordá que en nuestro estudio trabajamos solo con 3 camillas por clase para brindarte máxima atención.
   > 
   > ¿Te gustaría aprovechar el beneficio y agendar tus clases? ✨
4. Agregás los **Botones**:
   - Botón 1 (Respuesta rápida): `Quiero la promo`
   - Botón 2 (Respuesta rápida): `No por ahora`
   - Botón 3 (Baja obligatoria de Meta): `Detener avisos` *(Meta lo exige en marketing para proteger la reputación del remitente)*.
5. Das click en **Enviar a Revisión**. En 5 a 15 minutos Meta la deja en estado **Aprobada (Verde)**.

---

### Paso 2: Segmentar la Base de Datos (Regla Anti-Spam)
> [!CAUTION]
> **Nunca envíes una promo idéntica a toda la base sin segmentar.**
> Si le mandás una promo de "volvé al estudio" a una alumna que pagó ayer su cuota completa, genera confusión.

En el sistema podés dividir los destinatarios en 3 listas:
- **Lista A (Alumnas Inactivas):** Alumnas con cuenta que no reservan hace más de 30 días $\rightarrow$ Oferta de reincorporación.
- **Lista B (Prospectos Interesadas):** Personas que consultaron por WhatsApp pero nunca compraron abono $\rightarrow$ Invitación a clase de prueba.
- **Lista C (Alumnas Activas):** Alumnas que vienen hoy $\rightarrow$ Promo de renovación anticipada o traer a una amiga (2x1).

---

### Paso 3: Disparo Programado con Rate-Limiting (Espaciado)
Para evitar que los servidores de Meta o WhatsApp marquen el envío como comportamiento anómalo:
- El sistema envía los mensajes en cola con un intervalo de **2 a 3 segundos entre cada número**.
- Enviar 300 mensajes toma unos **10 a 15 minutos en total**.
- El límite de Meta en Tier 1 es de **1.000 destinatarios únicos por cada período de 24 horas** (mucho mayor a los 100-300 contactos usuales del estudio).

---

### Paso 4: Atención Automatizada de las Respuestas con la IA
Al enviar un broadcast de 200 mensajes, típicamente responden entre 30 y 60 personas en los primeros 30 minutos:
- En un estudio tradicional, la dueña colapsaría respondiendo mensajes uno a uno.
- En **Violett Pilates**, cada persona que responda o presione el botón *"Quiero la promo"* es atendida de inmediato por el **Asistente IA**:
  - Le muestra los horarios disponibles de las 3 camillas.
  - Le envía el alias para transferir.
  - Le recibe el comprobante y se lo envía a Débora para su confirmación en 1 click.
- En el panel de **Comunicaciones CRM (`/admin/comunicaciones`)**, Débora puede ver los chats en tiempo real y, si lo desea, activar el switch *"Pausar IA / Atender yo"* para responder personalmente a cualquier clienta especial.

---

## 7. Plan de Acción Recomendado para Implementar

1. **Alta de Plantillas en Meta:** Cargar en el panel de Meta las 18 plantillas de este catálogo (las operativas primero, luego las de marketing).
2. **Configurar Variables de Entorno en el VPS:**
   - `WHATSAPP_TOKEN=EAAG...` (Token permanente del sistema en Meta).
   - `WHATSAPP_PHONE_NUMBER_ID=109283...` (ID del número de Violett).
   - `WHATSAPP_BUSINESS_ACCOUNT_ID=...`
3. **Automatización Nocturna (Cron):**
   - 20:30 hs: Envío automático de cronograma a profesoras (`notificar_profesores_agenda_diaria`).
   - Cada 30 min: Monitoreo de cupos y recordatorios de turnos del día (`enviar_recordatorios_proactivos` y `cancelar_clases_bajo_cupo`).
4. **Prueba Piloto Controlada:** Enviar recordatorios primero al teléfono de Débora y de una profesora de prueba antes de abrir el envío a todas las alumnas.

---
*Documento elaborado para Violett Pilates Reformer • Ramos Mejía, Buenos Aires.*
