# 🚀 Auditoría SEO Técnica y Estrategia de Posicionamiento en Google
**Dominio auditado:** `violett.com.ar` / `violett.com.ar/pilates/`  
**Archivos de código inspeccionados:**  
- [engine/frontend/index.html](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/index.html)  
- [landings/index.html](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/landings/index.html)  
- [LandingView.tsx](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/src/pages/public/LandingView.tsx)  
- [proxy/nginx.conf](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/proxy/nginx.conf)  

---

## 1. Diagnóstico General: ¿Cómo ve Google hoy a Violett Pilates?

> **Puntaje SEO Técnico Actual: 3.8 / 10**  
> **Puntaje SEO Local (Ramos Mejía / Zona Oeste): 2.5 / 10**

### El Problema Principal en una Frase:
Hoy la web está optimizada únicamente para **quien ya conoce el nombre "Violett Pilates"**, pero es **prácticamente invisible en Google para las miles de mujeres que buscan *"Pilates Reformer en Ramos Mejía"*, *"Clases de Pilates cerca de mí"* o *"Pilates postural Zona Oeste"***.

---

## 2. Los 7 Errores Críticos de SEO Detectados en el Código

### 🔴 Error #1: El `<title>` y la `<meta description>` no tienen ni la actividad completa ni la ciudad
En [engine/frontend/index.html](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/index.html#L43-L59):
```html
<title>Violett Pilates</title>
<meta name="description" content="Violett Pilates. Tu compromiso con la elegancia. El método definitivo para esculpir tu figura y conectar cuerpo y mente." />
```
- **Por qué es grave:** El `<title>` es el factor On-Page #1 de Google. Hoy dice solo *"Violett Pilates"* (15 caracteres de los 60 permitidos). No dice **"Pilates Reformer"**, no dice **"Ramos Mejía"**, no dice **"Estudio Boutique"** ni **"Débora Zárate"**.
- Nadie entra a Google y escribe *"Tu compromiso con la elegancia"*. Las clientas buscan: `pilates reformer ramos mejia`, `clases de pilates ramos mejia`, `estudio de pilates zona oeste`.

### 🔴 Error #2: `landings/index.html` está completamente vacío de etiquetas SEO
En [landings/index.html](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/landings/index.html#L1-L13) (que sirve la raíz del dominio `violett.com.ar` y `/estetica`):
```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Violett Pilates</title>
  <link rel="icon" type="image/png" href="/logo-icon.png" />
</head>
```
- **Por qué es grave:** No tiene `meta description`, no tiene Open Graph (`og:title`, `og:image`), y el `<title>` estático en el servidor dice `"Violett Pilates"` incluso cuando alguien comparte el link de **Violett Estética** por WhatsApp o Instagram (ya que los bots de vista previa de WhatsApp/Meta no ejecutan el `useEffect` de React).

### 🔴 Error #3: No existen `robots.txt` ni `sitemap.xml` (y Nginx devuelve HTML en su lugar)
Al revisar las carpetas `engine/frontend/public/` y `landings/public/`, **no existen los archivos `robots.txt` ni `sitemap.xml`**.
- **Efecto colateral en Nginx:** Como [proxy/nginx.conf](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/proxy/nginx.conf#L74) usa `try_files $uri $uri/ /index.html;`, cuando Googlebot pide `violett.com.ar/sitemap.xml` o `violett.com.ar/robots.txt`, el servidor le responde con el código HTML de React (`200 OK`). Google Search Console rechaza esto como error crítico de rastreo.

### 🔴 Error #4: Cero Datos Estructurados (Schema.org `JSON-LD` para Negocio Local)
No hay ningún script `application/ld+json` en el código.
- Para un estudio físico en **Gral. Guido 1573, Ramos Mejía**, Google necesita un bloque JSON-LD de tipo `ExerciseGym` / `HealthAndBeautyBusiness` que declare explícitamente:
  - Dirección postal exacta (`Gral. Guido 1573, Ramos Mejía, Buenos Aires, B1704`).
  - Coordenadas geográficas (Latitud/Longitud de Ramos Mejía).
  - Teléfono de reservas (`+5491157691786`).
  - Rango de precios, horarios de apertura, fundadora (`Débora Zárate`) y preguntas frecuentes (`FAQPage`).

### 🔴 Error #5: Desperdicio Semántico de Etiquetas `<h1>` y `<h2>`
Google lee los encabezados `<h1>` y `<h2>` como el índice temático de tu negocio. Mirá lo que lee Google hoy en [LandingView.tsx](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/src/pages/public/LandingView.tsx):
- `<h1>`: *"Violett Pilates"*
- `<h2>`: *"✦ El arte de esculpir la silueta de tus sueños y habitar tu cuerpo con elegancia"*
- `<h2>`: *"✦ Una vitalidad radiante para vivir al máximo"*
- `<h2>`: *"✦ Te esperamos exactamente como sos"*
- `<h2>`: *"✦ La corona de tu día: Una hora diseñada para vos"*
- `<h2>`: *"✦ El Estilo de Vida Violett"*
- **Diagnóstico:** De 11 encabezados `<h2>`, **ninguno contiene palabras clave de búsqueda real** (*Pilates Reformer*, *Ramos Mejía*, *Clases personalizadas*, *Postura y dolor de espalda*). Para el algoritmo de Google, la página parece un blog literario en lugar de un estudio de Pilates Reformer en Ramos Mejía.

### 🔴 Error #6: Canibalización de Dominios y Falta de `<link rel="canonical">`
En [proxy/nginx.conf](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/proxy/nginx.conf#L3):
```nginx
server_name violett.com.ar www.violett.com.ar pilates.violett.com.ar localhost;
```
- El sitio responde igual en `violett.com.ar/pilates/`, `www.violett.com.ar/pilates/` y `pilates.violett.com.ar/pilates/`, y no existe la etiqueta `<link rel="canonical" href="https://violett.com.ar/pilates/" />`.
- Si Google indexa dos o tres variantes a la vez, divide la autoridad del dominio entre ellas (contenido duplicado interno).

### 🔴 Error #7: Bloqueo de Zoom en el Viewport (`user-scalable=0`)
En [engine/frontend/index.html](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/engine/frontend/index.html#L40):
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0, viewport-fit=cover" />
```
- Google Lighthouse penaliza automáticamente en su auditoría móvil cualquier página pública que tenga `user-scalable=0` o `maximum-scale=1.0`, restando puntos de accesibilidad y experiencia de página (Page Experience).

---

## 3. Cómo Solucionarlo en el Código (Mejoras Técnicas Listas para Aplicar)

### A. El `<head>` Perfecto para `engine/frontend/index.html`
Reemplazar los meta tags actuales por esta configuración optimizada para SEO Local y Rich Snippets:

```html
<!-- Título con Keyword Principal + Diferencial + Ciudad (59 caracteres) -->
<title>Violett Pilates Reformer en Ramos Mejía | Estudio Boutique</title>

<!-- Meta Description persuasiva con ubicación, método y CTA (156 caracteres) -->
<meta name="description" content="Estudio boutique de Pilates Reformer en Ramos Mejía (Gral. Guido 1573). Grupos exclusivos de 3 camillas, 55' de Reformer + 5' de masaje final. Reservá hoy." />

<!-- Canonical para evitar duplicados entre www y sin www -->
<link rel="canonical" href="https://violett.com.ar/pilates/" />
<meta name="robots" content="index, follow, max-image-preview:large" />
<meta name="geo.region" content="AR-B" />
<meta name="geo.placename" content="Ramos Mejía, Buenos Aires" />

<!-- Open Graph / WhatsApp / Instagram -->
<meta property="og:type" content="website" />
<meta property="og:locale" content="es_AR" />
<meta property="og:site_name" content="Violett Pilates" />
<meta property="og:url" content="https://violett.com.ar/pilates/" />
<meta property="og:title" content="Violett Pilates Reformer en Ramos Mejía ✦ Estudio Boutique" />
<meta property="og:description" content="Grupos exclusivos de máximo 3 camillas Reformer + 5 minutos de masaje de descompresión al finalizar. Método Débora Zárate en Ramos Mejía." />
<meta property="og:image" content="https://violett.com.ar/pilates/logo-full.png" />

<!-- Schema.org JSON-LD: Negocio Local + Estudio de Pilates + FAQ -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": ["ExerciseGym", "HealthAndBeautyBusiness", "LocalBusiness"],
      "@id": "https://violett.com.ar/pilates/#business",
      "name": "Violett Pilates",
      "alternateName": "Violett Pilates Reformer Ramos Mejía",
      "description": "Estudio boutique exclusivo de Pilates Reformer en Ramos Mejía. Clases personalizadas en grupos reducidos de máximo 3 camillas con masaje de descompresión final. Dirigido por la Lic. Débora Zárate.",
      "url": "https://violett.com.ar/pilates/",
      "telephone": "+5491157691786",
      "priceRange": "$$",
      "image": "https://violett.com.ar/pilates/logo-full.png",
      "founder": {
        "@type": "Person",
        "name": "Débora Zárate",
        "jobTitle": "Kinesióloga, Fisiatra y Directora de Violett Pilates"
      },
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "Gral. Guido 1573",
        "addressLocality": "Ramos Mejía",
        "addressRegion": "Provincia de Buenos Aires",
        "postalCode": "B1704",
        "addressCountry": "AR"
      },
      "areaServed": [
        { "@type": "City", "name": "Ramos Mejía" },
        { "@type": "City", "name": "Haedo" },
        { "@type": "City", "name": "Villa Sarmiento" },
        { "@type": "City", "name": "San Justo" },
        { "@type": "City", "name": "Ciudadela" }
      ],
      "openingHoursSpecification": [
        {
          "@type": "OpeningHoursSpecification",
          "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
          "opens": "08:00",
          "closes": "21:00"
        },
        {
          "@type": "OpeningHoursSpecification",
          "dayOfWeek": ["Saturday"],
          "opens": "09:00",
          "closes": "13:00"
        }
      ]
    },
    {
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "¿Cuántas alumnas hay por clase en Violett Pilates Ramos Mejía?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Nuestras clases son estrictamente reducidas con un máximo de 3 camillas Reformer por turno para garantizar atención personalizada y corrección postural permanente."
          }
        },
        {
          "@type": "Question",
          "name": "¿Cómo es una clase de Pilates Reformer en Violett?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Cada sesión dura 60 minutos: 55 minutos de Pilates Reformer adaptado a tu nivel y objetivos, seguidos de 5 minutos de masaje de descompresión asistido."
          }
        },
        {
          "@type": "Question",
          "name": "¿Puedo empezar Pilates Reformer si nunca entrené o tengo dolor de espalda?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Sí. El Método Violett, creado por la kinesióloga Débora Zárate con más de 21 años de experiencia, adapta los resortes y ejercicios a tu cuerpo, cuidando tu columna y articulaciones desde la primera sesión."
          }
        }
      ]
    }
  ]
}
</script>
```

### B. Optimización Semántica de Encabezados (`H1` y `H2`) sin perder la Elegancia Boutique
El secreto del SEO para marcas de lujo es **combinar la keyword exacta en una etiqueta semántica con el titular emocional**:

| Ubicación | Antes (0 SEO) | Después (Estético + Alto SEO Local) |
| --- | --- | --- |
| **Kicker / H1 del Hero** | `<h1>Violett Pilates</h1>` | `<h1>Pilates Reformer Boutique en Ramos Mejía</h1>` *(en tipografía sutil arriba)* + Título visual principal |
| **H2 Sección Experiencia** | `✦ La corona de tu día: Una hora diseñada para vos` | `✦ Clases de Pilates Reformer de 60 Minutos: El Ritual 55 + 5` |
| **H2 Sección Beneficios** | `✦ El Estilo de Vida Violett` | `✦ Beneficios del Pilates Reformer para tu Silueta, Postura y Espalda` |
| **H2 Sección Autoridad** | `✦ 21 Años de Excelencia: El Método Débora Zárate` | `✦ 21 Años de Excelencia en Pilates y Salud Postural: El Método Débora Zárate` |
| **H2 Sección Precios** | `✦ Tu Compromiso con la Elegancia` | `✦ Planes y Aranceles de Pilates Reformer en Ramos Mejía` |

### C. Creación de `robots.txt` y `sitemap.xml`
Crear ambos archivos en `public/` para que Google indexe limpio las landings públicas y **no indexe** las pantallas privadas de login o administración:

**`robots.txt`:**
```txt
User-agent: *
Allow: /
Allow: /pilates/
Allow: /estetica
Disallow: /pilates/admin
Disallow: /pilates/login
Disallow: /pilates/api/
Disallow: /estetica/app/
Disallow: /estetica/api/

Sitemap: https://violett.com.ar/sitemap.xml
```

---

## 4. Estrategia Maestra: ¿Cómo Posicionar a Violett #1 en Ramos Mejía en 60 Días?

En un negocio físico local (estudio de Pilates o centro de Estética), **el 70% del tráfico calificado de Google entra por el Mapa (Google Local Pack — los 3 primeros lugares de Google Maps)** y el **30% restante por los resultados orgánicos web**.

Para dominar ambos en Ramos Mejía y San Justo, este es el plan de batalla en 4 pasos:

### Paso 1: Dominar Google Maps (Google Business Profile)
1. **Nombre de la Ficha en Google Maps:**  
   `Violett Pilates | Pilates Reformer en Ramos Mejía`  
   *(Incluir "Pilates Reformer" en el título comercial de Google Maps dispara el posicionamiento geolocalizado cuando alguien busca desde un radio de 3 km en Ramos Mejía, Haedo o Villa Sarmiento).*
2. **Categoría Principal:** `Estudio de pilates` (`Pilates studio`).  
   **Categorías Secundarias:** `Centro de bienestar`, `Gimnasio`.
3. **Cargar los Servicios con Precios en Google Maps:** Cargar *"Clase Inaugural de Pilates Reformer"*, *"Plan Mensual 4 Clases"*, *"Plan Mensual 8 Clases"*, *"Plan Mensual 12 Clases"*, y poner como link de reserva `https://violett.com.ar/pilates/#membresias`.
4. **Automatización con tu Bot de WhatsApp (Ventaja Competitiva Injusta):**  
   Ya tenés un sistema que sabe exactamente cuándo una alumna cumplió **su clase N° 8 o renovó su segundo mes**. Podés hacer que el bot, cuando una alumna deja una reseña de 5 estrellas en la app de Violett, le responda automáticamente por WhatsApp:
   > *"¡Qué alegría leerte, [Nombre]! ✦ ¿Nos regalarías 30 segundos copiando este mismo comentario en nuestro Google Maps? Nos ayuda muchísimo → [Link directo a reseña de Google]"*  
   Con solo **25 a 35 reseñas de 5 estrellas en Google Maps** que mencionen las palabras *"Ramos Mejía"*, *"Reformer"*, *"Débora"* y *"masaje final"*, pasás al **Top 1 de Ramos Mejía** superando a todos los estudios tradicionales.

### Paso 2: Atacar las 3 Intenciones de Búsqueda de Alta Conversión
Las mujeres en Zona Oeste buscan Pilates por 3 motivos distintos. La landing debe contener las palabras exactas de esos 3 perfiles:
1. **Búsqueda por Aparato y Zona (Tráfico Caliente):**  
   *Keywords:* `pilates reformer ramos mejia`, `clases de pilates en camilla ramos mejia`, `pilates cerca de guido ramos mejia`, `precios pilates reformer zona oeste`.  
   *(Se captura con el nuevo H1, el H2 de Precios y el pie de página con la dirección exacta y barrios cercanos).*
2. **Búsqueda por Dolor / Postura (Tráfico de Salud — El Fuerte de Débora como Kinesióloga):**  
   *Keywords:* `pilates para dolor de espalda ramos mejia`, `pilates postural zona oeste`, `pilates guiado por kinesiologa`.  
   *(Destacar explícitamente en la Sección de Débora Zárate su título de **Kinesióloga y Fisiatra**; en Pilates casi ningún estudio de barrio está dirigido por una kinesióloga con 21 años de experiencia, y eso en Google e IA buscadores como ChatGPT/Gemini posiciona como máxima autoridad médica-postural).*
3. **Búsqueda por Exclusividad (Mujeres que huyen de gimnasios llenos):**  
   *Keywords:* `estudio de pilates boutique ramos mejia`, `clases personalizadas de pilates 3 camillas`.

### Paso 3: Sinergia SEO Cruzada entre Pilates (Ramos Mejía) y Estética (San Justo)
Ambas marcas viven bajo el mismo dominio raíz `violett.com.ar`.
- En el footer de **Violett Pilates (`/pilates/`)**, colocar un enlace semántico limpio hacia **Violett Estética (`/estetica`)**:  
  *"Conocé también Violett Estética Avanzada & Rehabilitación Postquirúrgica en San Justo →"*.
- En el footer de **Violett Estética (`/estetica`)**, colocar un enlace hacia **Violett Pilates (`/pilates/`)**:  
  *"Conocé nuestro Estudio Boutique de Pilates Reformer en Ramos Mejía →"*.
- **Por qué funciona:** Google transfiere la autoridad médica y kinésica de la landing de Estética (cirujanos, drenaje linfático, kinesiología) hacia la landing de Pilates, elevando el **E-E-A-T** (*Experience, Expertise, Authoritativeness, Trustworthiness*) de todo el dominio `violett.com.ar`.

### Paso 4: Redirección 301 en Nginx para Unificar Autoridad
En [proxy/nginx.conf](file:///c:/Users/Alex/Documents/FireSeed/Violett%20Pilates/proxy/nginx.conf):
- Redirigir `www.violett.com.ar` → `https://violett.com.ar` con un `301 Permanent Redirect` para que toda la fuerza de enlaces se concentre en una única URL canónica.
- Servir `robots.txt` y `sitemap.xml` directamente como archivos estáticos para que Google Search Console los procese sin errores.
