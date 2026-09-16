# Historial de Funcionalidades y Soluciones (Changelog)

Este documento sirve como registro oficial de las funcionalidades, bugs y correcciones aplicadas a la plataforma (tanto en el motor core como en la instancia de Violett Pilates). Revisar este historial te ayudarǭ a entender quǭ cosas ya deberan estar solucionadas y dnde acudir si vuelven a fallar.

## ltimas Correcciones (Septiembre 2026)

### 1. Auto-cǭlculo de Hora Fin al crear Turnos
- **Problema**: Al seleccionar una "Hora Inicio" en el panel de creacin de turnos puntuales (o plantillas), la "Hora Fin" no se calculaba sola si el usuario an no haba seleccionado una clase.
- **Causa**: El mtodo interno exiga que existiera una `clase` seleccionada para buscar su `duracion_minutos`. Al estar vaca, ignoraba el cǭlculo.
- **Solucin**: Se actualiz la condicin en `AgendaAdmin.tsx` y `PlantillaForm.tsx` para que si no hay clase seleccionada asuma `60` minutos por defecto y auto-calcule igual.
- **Estado**: **Solucionado**.

### 2. Pǭgina en Blanco (Crash) al navegar rǭpido entre pestaas
- **Problema**: Ir de Inicio -> Reservas -> Inicio generaba que la pantalla quedara completamente en blanco bajo el header.
- **Causa**: El mdulo `AnimatePresence` de Framer Motion colisionaba intentando montar y desmontar mltiples `Layouts` al mismo tiempo en clics rǭpidos, lo que terminaba desmontando toda la app.
- **Solucin**: Se retir `AnimatePresence` del enrutador principal (`ClientLayout.tsx`), dejando slo la animacin de entrada, logrando navegacin instantǭnea, estable y sin posibilidad de choque.
- **Estado**: **Solucionado**.

### 3. Filtro de Reservas en "Mis Reservas"
- **Problema**: La pestaa no mostraba las reservas a las que el cliente estaba anotado.
- **Causa**: El frontend filtraba buscando la variable `estado === 'RESERVADO'`, que no se enva en el endpoint normal de turnos. 
- **Solucin**: Se cambi la lgica a usar `isBookedByMe` (propiedad oficial).
- **Estado**: **Solucionado**.

### 4. Error 404 en el Historial de Clases
- **Problema**: Apretar el botn "Ver clases a las que asist" en Mis Reservas tiraba error 404 en consola.
- **Causa**: La funcin de historial exista en el backend, pero la ruta `reservas/historial/` no haba sido inscripta en `urls.py`.
- **Solucin**: Ruta mapeada correctamente.
- **Estado**: **Solucionado**.

### 5. Clases Particulares Manuales aparecan "Llenas"
- **Problema**: Al crear un turno desde Admin sin especificar cupo_actual, el modelo de Django asignaba por defecto `0`, dejando la clase sin lugares desde el minuto 1.
- **Causa**: Una falla de condicin usando identificadores UUID automǭticos haca que el guardado omitiera re-calcular los lugares basado en el cupo_maximo.
- **Solucin**: Se reemplaz `if not self.pk` por `if self._state.adding` en `models.py`.
- **Estado**: **Solucionado**.

### 6. Error 500 al Registrarse (allauth missing config)
- **Problema**: Al intentar crear una cuenta nueva en la pantalla de registro, el servidor arrojaba un "Error 500 (Internal Server Error)".
- **Causa**: El mdulo `django-allauth` intentaba validar un campo `username` por defecto, pero nuestro modelo de Usuario personalizado elimin el campo `username` a favor de usar slo `email`. Al no encontrar configurada la excepcin `ACCOUNT_USERNAME_REQUIRED = False` ni `ACCOUNT_AUTHENTICATION_METHOD = 'email'` en `settings.py`, el motor colapsaba al intentar validar el nombre de usuario inexistente.
- **Solucin**: Se aadieron explcitamente estas dos configuraciones en `settings.py` para forzar la autenticacin 100% por email y desactivar la validacin de username.
- **Estado**: **Solucionado** (Registrado histricamente).

---


## Auditora: Violett Pilates vs Engine Original

Se realiz una revisin lnea por lnea entre `engine-booking-core` y `Violett Pilates`.
**Veredicto**: Los supuestos "bugs que volvieron" (regresiones por copiar mal el cdigo) en realidad **no son regresiones**. 
El error del auto-cǭlculo de la hora fin (por falta de seleccionar clase) exista exactamente igual en ambos proyectos (tanto en el *engine original* como en la app). Nunca haba sido cubierto ese caso borde, slo pareca funcionar antes porque quizǭs probabas seleccionando la clase primero y luego el horario.

### ¿Quǭ s es diferente entre ambos proyectos?
- Los colores, assets (imǭgenes, manifiestos PWA) y textos ("Violett", "Demo Studio").
- Ciertos filtros y roles adaptados.
- Las migraciones en las bases de datos locales (`db.sqlite3` separados).

> **Nota para el futuro**: Cada vez que reparemos un bug importante de la lgica base, se anotarǭ aqu y (si corresponde) se migrarǭ al engine original para que no vuelva a heredarse roto a clientes nuevos.

### 15 de Septiembre 2026 - Fixes de Despliegue y Autenticación en Producción

**Error:** Nginx en los contenedores frontend no arrancaba, quedando en ciclo de reinicio continuo, devolviendo error 502 Bad Gateway en Cloudflare.
**Causa:** El archivo 
ginx.conf del frontend fue guardado desde Windows con codificación UTF-8 con BOM (Byte Order Mark). Nginx en Linux (Alpine) no soporta el caracter invisible U+FEFF al inicio del archivo y crasheaba con error de sintaxis en la línea 1.
**Solución:** Se eliminó el BOM guardando el archivo estrictamente como UTF-8 sin marca de orden de bytes.

**Error:** Los frontends se mezclaron tras el despliegue; al ingresar a /pilates/app/login el navegador descargaba el HTML de la estética, intentaba pedir archivos JavaScript de /estetica/app/assets/ y terminaba en pantalla blanca (Error 404).
**Causa:** Al estar construidos sobre el mismo Dockerfile y context, y no tener nombres de imagen asignados explícitamente en docker-compose.yml, Docker BuildKit reutilizó capas de caché de manera cruzada.
**Solución:** Se asignaron identificadores image: explícitos en el docker-compose.yml (iolettpilates-frontend-pilates y iolettpilates-frontend-estetica) y se agregó la bandera --no-cache en el script subir_a_prod.sh para forzar la independencia absoluta de ambos builds.

**Error:** Error 500 (Internal Server Error) al intentar registrar un nuevo usuario desde el frontend. La UI mostraba un listado de índices numéricos y caracteres (ej: 70: t | 71: i).
**Causa:** 
1. La UI mostraba símbolos raros porque el backend respondía con la página HTML por defecto de Django Server Error (500) en vez de JSON, y el frontend la procesaba iterando los caracteres (string) al intentar mapear los errores.
2. El error 500 subyacente ocurría porque librerías internas de autenticación (dj-rest-auth y llauth) ejecutaban código de validación asumiendo campos o variables de estado que entraban en conflicto con la ausencia total del campo username en nuestra base de datos. Además, el serializador intentaba guardar campos inexistentes (echa_nacimiento, contacto_emergencia) al vuelo.
**Solución:** 
1. Se limpió CustomRegisterSerializer para que solo parsee los campos que realmente existen en el modelo Usuario.
2. Se implementó un CustomAccountAdapter propio para interceptar la lógica de llauth y evitar crasheos por la ausencia del username.
3. Se envolvió el método save() del registro en un 	ry/except que atrapa cualquier excepción crítica y la devuelve forzadamente como un error 400 (Bad Request) en formato JSON, para que el frontend nunca vuelva a romperse imprimiendo un HTML letra por letra.

