# Cómo crear un chatbot con IA para tu web (sin experiencia previa)

## Guía paso a paso para crear un asistente virtual que responda preguntas sobre tu perfil profesional

---

## Tabla de contenidos

1. [Introducción](#1-introducción)
2. [Requisitos previos](#2-requisitos-previos)
3. [Paso 1: Obtener la API Key de Google Gemini](#3-paso-1-obtener-la-api-key-de-google-gemini)
4. [Paso 2: Crear el Google Apps Script (el proxy)](#4-paso-2-crear-el-google-apps-script-el-proxy)
5. [Paso 3: Almacenar secretos en el Google Apps Script](#5-paso-3-almacenar-secretos-en-el-google-apps-script)
6. [Paso 4: Desplegar el Google Apps Script](#6-paso-4-desplegar-el-google-apps-script)
7. [Paso 5: Crear la estructura de archivos](#7-paso-5-crear-la-estructura-de-archivos)
8. [Paso 6: El HTML — Integrar el chatbot en tu web](#8-paso-6-el-html--integrar-el-chatbot-en-tu-web)
9. [Paso 7: El CSS — Estilos del chatbot](#9-paso-7-el-css--estilos-del-chatbot)
10. [Paso 8: El JavaScript — Lógica del chatbot](#10-paso-8-el-javascript--lógica-del-chatbot)
11. [Paso 9: Logging de preguntas en Google Sheets (opcional)](#11-paso-9-logging-de-preguntas-en-google-sheets-opcional)
12. [Personalización](#12-personalización)
13. [Solución de problemas](#13-solución-de-problemas)

---

## 1. Introducción

### ¿Qué es esto?

Vamos a crear un **chatbot con inteligencia artificial** que se integre en tu
página web. Cuando alguien visite tu web, podrá abrir un chat y preguntar sobre
tu perfil profesional, experiencia, formación, etc. El chatbot responderá usando
la información que tú le proporciones.

### ¿Cómo funciona?

El sistema tiene **3 partes**:

```
┌─────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│  NAVEGADOR   │ ───> │  GOOGLE APPS SCRIPT  │ ───> │  GOOGLE GEMINI  │
│  (tu web)    │ <─── │  (proxy seguro)      │ <─── │  (la IA)        │
└─────────────┘      └──────────────────────┘      └─────────────────┘
```

1. **El navegador** (la web del usuario) envía la pregunta al Google Apps Script
2. **El Google Apps Script** añade la clave de API de Gemini (que está guardada
   como secreta en el Script) y la reenvía a Google Gemini
3. **Google Gemini** procesa la pregunta con la información del CV y devuelve
   una respuesta
4. La respuesta viaja de vuelta al navegador

**¿Por qué no llamar a Gemini directamente desde el navegador?**

Porque la clave de API quedaría expuesta en el código fuente de la web. Cualquiera
que sepa un poco de programación podría verla y usarla. El Google Apps Script hace
de intermediario seguro: la clave nunca sale del servidor de Google.

### ¿Qué tiene este chatbot?

- Burbuja flotante con avatar del bot
- Panel de chat con animaciones suaves
- Respostas formateadas (negrita, cursiva, listas, enlaces)
- Mensaje amigable cuando se alcanzan los límites de la API
- Logging de preguntas en Google Sheet con IP del usuario
- Diseño responsive para móvil
- Sistema de fallback entre modelos de Gemini

### ¿Qué coste tiene?

- **Google Gemini**: tier gratuito con uso generoso (no necesitas tarjeta)
- **Google Apps Script**: gratuito hasta 90 minutos de ejecución al día
- **GitHub Pages** (hosting): gratuito para sitios públicos
- **api.ipify.org**: gratuito (para obtener la IP del usuario)

---

## 2. Requisitos previos

### Cuentas que necesitas crear (todas gratuitas)

| Servicio | Para qué | Enlace |
|----------|----------|--------|
| Google | API Key de Gemini + Apps Script + Sheets | https://accounts.google.com |
| GitHub | Subir tu código y publicar la web | https://github.com |

### Herramientas que necesitas instalar

| Herramienta | Para qué | Enlace |
|-------------|----------|--------|
| VS Code | Editor de código (recomendado) | https://code.visualstudio.com |
| Git | Subir cambios a GitHub | https://git-scm.com |
| Navegador | Chrome, Firefox o Edge | Ya lo tienes |

### Conocimientos mínimos

No necesitas ser programador, pero sí entender:
- Qué es un archivo HTML y cómo se edita
- Qué es un archivo CSS (aunque sea a nivel básico)
- Qué es un archivo JavaScript (aunque sea a nivel básico)
- Cómo funciona la terminal/consola (para git)

---

## 3. Paso 1: Obtener la API Key de Google Gemini

La API Key es como una contraseña que le dice a Google "soy yo, déjame usar
tu inteligencia artificial". Sin ella, el chatbot no puede funcionar.

### 3.1 Crear la clave

1. Abre tu navegador y ve a: **https://aistudio.google.com/apikey**
2. Inicia sesión con tu cuenta de Google
3. Haz clic en **"Create API key"** (Crear clave de API)
4. Selecciona un proyecto existente o crea uno nuevo (da igual)
5. Se generará una clave que empieza por algo como `AIza...`
6. **Cópiala y guárdala en un sitio seguro** (la necesitarás después)

### 3.2 Restringir la clave (recomendado por seguridad)

Aunque esta clave va a estar protegida por el proxy, es buena práctica
restringirla para que solo funcione desde tu web:

1. En la misma página, haz clic en **"Edit API key"** (editar) junto a tu clave
2. En **"API restrictions"**, selecciona **"Restrict key"**
3. En **"HTTP referrers"**, añade tu dominio:
   - Si usas GitHub Pages: `valenfer.github.io/*`
   - Si tienes tu propio dominio: `tudominio.com/*`
4. Haz clic en **"Save"**

> **¿Qué hace esto?** Aunque alguien vea tu clave en el código fuente, solo
> funcionará cuando la petición venga desde tu web. Si alguien la intenta
> usar desde otro sitio, Google la rechazará.

### 3.3 Límites de la cuenta gratuita

Los límites de la cuenta gratuita varían según el modelo. Consulta la tabla
actualizada en: https://ai.google.dev/gemini-api/docs/rate-limits

Como referencia (agos 2026):

| Modelo | RPM (por min) | TPM (tokens/min) | RPD (por día) |
|---|---|---|---|
| gemini-3.6-flash | ~10 | ~3M | ~1,500 |
| gemini-3.5-flash | ~10 | ~3M | ~1,500 |
| gemini-1.5-flash | 15 | 1,000,000 | 1,500 |

> **IMPORTANTE:** Google depreca modelos frecuentemente. Si ves errores de
> "modelo no disponible", consulta https://ai.google.dev/gemini-api/docs/models
> para ver los modelos actuales.

---

## 4. Paso 2: Crear el Google Apps Script (el proxy)

Google Apps Script es un servicio de Google que nos permite ejecutar código
JavaScript en los servidores de Google. Lo usaremos como proxy seguro para
llamar a la API de Gemini sin exponer la clave.

### 4.1 Crear el proyecto

1. Ve a: **https://script.google.com**
2. Haz clic en **"New project"** (Nuevo proyecto)
3. Verás un editor con una función vacía llamada `myFunction`
4. En la esquina superior izquierda, donde dice "Untitled project", haz clic
   y renómbralo a **"AIDA Proxy"** (o el nombre que quieras)

### 4.2 Pegar el código

Borra todo el código que hay por defecto y pega este **completo**:

```javascript
// ============================================================
// AIDA PROXY - Google Apps Script
// ============================================================
// Este script actúa como intermediario seguro entre tu web y
// la API de Google Gemini. La clave de API se almacena aquí
// (en las propiedades del Script) y nunca se expone al navegador.
//
// Además, registra cada pregunta/respuesta en un Google Sheet
// para que puedas ver qué preguntan los visitantes de tu web.
// ============================================================

// ------------------------------------------------------------
// doPost(e)
// ------------------------------------------------------------
// Función principal que se ejecuta cuando tu web envía una
// petición POST al Script.
//
// Parámetros:
//   e - Objeto que contiene los datos enviados desde la web
//       e.postData.contents - El cuerpo de la petición en formato texto
//
// Esta función decide qué hacer según el campo "action":
//   - Si action es "chat" → envía la pregunta a Gemini y devuelve la respuesta
//   - Si action es "log"  → guarda la pregunta en un Google Sheet
// ------------------------------------------------------------
function doPost(e) {
  try {
    // Convertir el texto recibido a un objeto JavaScript
    const data = JSON.parse(e.postData.contents);

    // Si la acción es "chat", llamar al proxy de Gemini
    if (data.action === 'chat') {
      return proxyGemini(data);
    }

    // Para cualquier otra acción (como "log"), guardar en el Sheet
    return logPregunta(data);
  } catch (err) {
    // Si hay error al parsear el JSON o en cualquier función,
    // devolver el error a la web
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ------------------------------------------------------------
// proxyGemini(data)
// ------------------------------------------------------------
// Esta es la función que realmente llama a la API de Gemini.
//
// Recibe los datos del chat (mensajes, configuración) y:
//   1. Lee la API Key de las propiedades secretas del Script
//   2. Construye la petición a Gemini
//   3. La envía usando UrlFetchApp
//   4. Devuelve la respuesta a tu web
//
// Parámetros:
//   data - Objeto con estos campos:
//     data.model          - Nombre del modelo de Gemini a usar
//     data.messages       - Array de mensajes de la conversación
//     data.systemInstruction - Instrucciones del sistema (el "prompt" del bot)
//     data.generationConfig  - Configuración (temperatura, tokens máximos)
// ------------------------------------------------------------
function proxyGemini(data) {
  // Leer la API Key desde las propiedades secretas del Script.
  // Si no está configurada, devolver error.
  const API_KEY = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  if (!API_KEY) {
    return ContentService
      .createTextOutput(JSON.stringify({
        ok: false,
        error: 'GEMINI_API_KEY no configurada en Script Properties'
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Seleccionar el modelo de Gemini (por defecto gemini-3.6-flash)
  const modelo = data.model || 'gemini-3.6-flash';

  // Construir la URL de la API de Gemini
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelo}:generateContent?key=${API_KEY}`;

  // Construir el cuerpo de la petición
  const payload = {
    contents: data.messages || [],                    // Historial de mensajes
    systemInstruction: data.systemInstruction || undefined, // Instrucciones del sistema
    generationConfig: data.generationConfig || {      // Configuración de generación
      temperature: 0.7,   // Creatividad (0.0 = muy preciso, 1.0 = muy creativo)
      maxOutputTokens: 1024 // Longitud máxima de la respuesta
    }
  };

  // Enviar la petición a Google Gemini
  // UrlFetchApp es el servicio de Google Apps Script para hacer peticiones HTTP
  // muteHttpExceptions: true → no lanza error si el servidor devuelve código 4xx o 5xx
  const response = UrlFetchApp.fetch(url, {
    method: 'POST',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  // Convertir la respuesta de texto a objeto JavaScript
  const result = JSON.parse(response.getContentText());

  // Devolver la respuesta a tu web
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true, data: result }))
    .setMimeType(ContentService.MimeType.JSON);
}

// ------------------------------------------------------------
// logPregunta(data)
// ------------------------------------------------------------
// Guarda cada pregunta, respuesta e IP en un Google Sheet.
// Esto te permite ver qué preguntan los visitantes de tu web.
//
// Parámetros:
//   data - Objeto con estos campos:
//     data.pregunta - La pregunta del usuario
//     data.respuesta - La respuesta del chatbot
//     data.modelo - Modelo de Gemini usado
//     data.url - URL de la página donde se hizo la pregunta
//     data.ip - Dirección IP del usuario
// ------------------------------------------------------------
function logPregunta(data) {
  try {
    // Leer el ID del Spreadsheet desde las propiedades
    const props = PropertiesService.getScriptProperties();
    const spreadsheetId = props.getProperty('SPREADSHEET_ID');

    // Solo guardar si hay un Spreadsheet configurado
    if (spreadsheetId) {
      const sheet = SpreadsheetApp.openById(spreadsheetId).getActiveSheet();

      // Añadir una fila con: fecha, pregunta, respuesta, modelo, URL, IP
      sheet.appendRow([
        new Date(),           // Fecha y hora de la pregunta
        data.pregunta || '',  // La pregunta del usuario
        data.respuesta || '', // La respuesta del chatbot
        data.modelo || '',    // Modelo de Gemini usado
        data.url || '',       // Página donde se hizo la pregunta
        data.ip || ''         // IP del usuario
      ]);
    }

    // Devolver confirmación
    return ContentService
      .createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ------------------------------------------------------------
// doGet()
// ------------------------------------------------------------
// Función que se ejecuta cuando alguien visita la URL del
// Script directamente en el navegador (petición GET).
// Sirve para comprobar que el Script está activo.
// ------------------------------------------------------------
function doGet() {
  return ContentService
    .createTextOutput('AIDA Proxy activo')
    .setMimeType(ContentService.MimeType.TEXT);
}
```

### 4.3 Guardar

Haz clic en el icono de floppy disk (💾) o pulsa **Ctrl + S** para guardar.

---

## 5. Paso 3: Almacenar secretos en el Google Apps Script

Las API Keys y los IDs **nunca** se escriben directamente en el código. Se guardan
en las "Script Properties" (propiedades del Script), que son como variables secretas
solo accesibles desde el editor de Apps Script.

### 5.1 Abrir propiedades

1. En el editor de Google Apps Script, haz clic en el icono de **engranaje**
   (⚙️) en la barra lateral izquierda, o ve a **File > Project settings**
2. Baja hasta la sección **"Script properties"**
3. Haz clic en **"Add script property"** (Añadir propiedad)

### 5.2 Añadir la API Key de Gemini

| Propiedad | Valor |
|-----------|-------|
| `GEMINI_API_KEY` | `AIza...` (la clave que copiaste en el Paso 1) |

### 5.3 Añadir el Spreadsheet ID (para logging, opcional)

Si quieres registrar las preguntas en un Google Sheet:

| Propiedad | Valor |
|-----------|-------|
| `SPREADSHEET_ID` | `El ID de tu Google Sheet` (ver Paso 9) |

Haz clic en **"Save"**.

> **IMPORTANTE:** Estas propiedades solo son visibles desde el editor de Apps Script.
> Nunca se envían al navegador. Son seguras.

---

## 6. Paso 4: Desplegar el Google Apps Script

Un Script guardado no es accesible desde fuera. Hay que "desplegarlo" (hacer
que tenga una URL pública a la que tu web pueda enviar peticiones).

### 6.1 Crear el despliegue

1. Haz clic en el botón azul **"Deploy"** (Desplegar) en la esquina superior derecha
2. Selecciona **"New deployment"** (Nuevo despliegue)
3. Haz clic en el icono de engranaje (⚙️) junto a "Select type"
4. Selecciona **"Web app"**
5. Rellena:
   - **Description**: "AIDA Proxy" (o lo que quieras)
   - **Execute as**: **Me** (tu cuenta)
   - **Who has access**: **Anyone** (cualquier usuario)
6. Haz clic en **"Deploy"**

### 6.2 Autorizar permisos

La primera vez que despliegas, Google te pide autorización:

1. Haz clic en **"Authorize access"**
2. Selecciona tu cuenta de Google
3. Si ves "Google hasn't verified this app", haz clic en **"Advanced"**
4. Luego haz clic en **"Go to AIDA Proxy (unsafe)"**
5. Acepta los permisos
6. Copia la **URL del despliegue** — se ve algo como:
   ```
   https://script.google.com/macros/s/AKfycb...xxxxx/exec
   ```

### 6.3 Autorizar permisos de red (IMPORTANTE)

Si al probar el chatbot sale error "No tienes permiso para llamar a UrlFetchApp.fetch":

1. En el editor, selecciona la función **`proxyGemini`** en el selector de funciones
2. Haz clic en **"Run"** (Ejecutar)
3. Si pide autorización, autorízala
4. Vuelve a desplegar (Deploy > Manage deployments > Edit > Nueva versión > Deploy)

> **¿Por qué?** Google Apps Script necesita permiso explícito para hacer
> peticiones HTTP externas. Ejecutar la función desde el editor activa ese permiso.

### 6.4 Guarda la URL

**Copia la URL del despliegue** y guárdala. La necesitarás en el Paso 8.

> **IMPORTANTE:** Cada vez que cambias algo en el Script y quieres que surta
> efecto, debes:
> 1. Guardar el código (Ctrl+S)
> 2. Deploy > Manage deployments > Edit (lápiz) > Nueva versión > Deploy

---

## 7. Paso 5: Crear la estructura de archivos

### Estructura de carpetas

```
curriculum/
├── css/
│   └── chatbot.css      ← Estilos del chatbot
├── img/
│   └── aidaico.png      ← Icono del chatbot (avatar)
├── js/
│   └── chatbot.js       ← Lógica del chatbot
└── index.html           ← Tu página web
```

### Archivos necesarios

| Archivo | Descripción |
|---------|-------------|
| `index.html` | Tu página web existente (ya la tienes) |
| `css/chatbot.css` | Los estilos del widget de chat |
| `js/chatbot.js` | El código JavaScript que hace funcionar el chat |
| `img/aidaico.png` | Una imagen cuadrada para el avatar del bot (40x40 o más) |

> **Nota:** Si tu web ya tiene un CSS y un JS propios, los archivos del chatbot
> se añaden sin modificar los existentes.

---

## 8. Paso 6: El HTML — Integrar el chatbot en tu web

Solo necesitas añadir **2 cosas** a tu HTML existente:

### 8.1 El contenedor del chatbot

Justo **antes del cierre de `</body>`**, añade este div:

```html
<!-- ============================================================
     CONTENEDOR DEL CHATBOT
     ============================================================
     Este div vacío es el "contenedor" donde JavaScript va a
     crear dinámicamente toda la interfaz del chatbot (burbuja,
     panel de chat, input, etc.).

     ¿Por qué un div vacío? Porque es más limpio: todo el HTML
     del chatbot se genera desde JavaScript, así que solo
     necesitas este punto de anclaje.
     ============================================================ -->
<div id="chatbot-root"></div>
```

### 8.2 Los scripts

**Después** del `div`, añade la referencia al archivo JavaScript del chatbot:

```html
<!-- ============================================================
     SCRIPTS DEL CHATBOT
     ============================================================ -->
<!-- chatbot.js contiene toda la lógica del widget de chat.
     El atributo "defer" hace que se cargue después de que el
     HTML esté listo, pero antes de que se dispare el evento
     DOMContentLoaded. Esto asegura que el DOM existe cuando
     JavaScript intenta crear los elementos del chatbot. -->
<script src="./js/chatbot.js" defer></script>
```

### 8.3 Ejemplo completo

Si tu `</body>` actualmente se ve así:

```html
    <footer>
        <p>Mi web</p>
    </footer>
</body>
</html>
```

Debe quedar así:

```html
    <footer>
        <p>Mi web</p>
    </footer>

    <!-- Contenedor del chatbot -->
    <div id="chatbot-root"></div>

    <!-- Lógica del chatbot -->
    <script src="./js/chatbot.js" defer></script>
</body>
</html>
```

### 8.4 Enlace al CSS del chatbot

En el `<head>` de tu HTML, añade el CSS del chatbot **después** de tu CSS
principal (para que puedas sobreescribir estilos si hace falta):

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Tu CSS principal primero -->
    <link rel="stylesheet" href="./css/styles.css">
    <!-- CSS del chatbot después -->
    <link rel="stylesheet" href="./css/chatbot.css">
    <title>Mi web</title>
</head>
```

---

## 9. Paso 7: El CSS — Estilos del chatbot

Crea el archivo `css/chatbot.css` con este contenido **comentado**:

```css
/* ============================================================
   CHATBOT CSS - Estilos del widget AIDA
   ============================================================
   Este archivo define todos los estilos visuales del chatbot:
   - La burbuja flotante en la esquina inferior derecha
   - El panel de chat que se abre al hacer clic
   - Los mensajes del bot y del usuario
   - El indicador de "escribiendo..."
   - El campo de entrada y botón de enviar
   - La animación de pulso para llamar la atención
   - Estilos para texto formateado (negrita, listas, enlaces)
   - Diseño responsive para móviles

   Los colores usan variables CSS (var(--accent), var(--bg), etc.)
   que deben estar definidas en tu CSS principal (styles.css).
   Si no las tienes, consulta la sección de personalización al
   final de este documento.
   ============================================================ */


/* ============================================================
   BURBUJA FLOTANTE
   ============================================================
   Es el círculo que aparece fijo en la esquina inferior derecha.
   Contiene el avatar del bot y los iconos de chat/cerrar.
   ============================================================ */

.chatbot-burbuja {
  position: fixed;
  bottom: 25px;
  right: 25px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 25px rgba(0, 212, 170, 0.4);
  z-index: 9999;
  transition: transform 0.3s, box-shadow 0.3s;
}

/* ============================================================
   AVATAR DEL BOT (imagen dentro de la burbuja)
   ============================================================ */

.chatbot-burbuja-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
  opacity: 1;
  transition: opacity 0.3s;
}

.chatbot-burbuja.abierta .chatbot-burbuja-avatar {
  opacity: 0;
}

/* ============================================================
   EFECTO HOVER EN LA BURBUJA
   ============================================================ */
.chatbot-burbuja:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 35px rgba(0, 212, 170, 0.6);
}

/* ============================================================
   ICONOS SVG DENTRO DE LA BURBUJA
   ============================================================ */

.chatbot-burbuja svg {
  width: 28px;
  height: 28px;
  fill: var(--bg);
  transition: transform 0.3s;
  position: relative;
  z-index: 1;
}

.chatbot-burbuja.abierta svg.icono-chat {
  display: none;
}

.chatbot-burbuja:not(.abierta) svg.icono-cerrar {
  display: none;
}

.chatbot-burbuja:not(.abierta) svg.icono-chat {
  display: none;
}

.chatbot-burbuja.abierta {
  background: var(--card);
  border: 1px solid var(--border);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.chatbot-burbuja.abierta svg.icono-cerrar {
  display: block;
  fill: var(--fg);
}

/* ============================================================
   ANIMACIÓN DE PULSO
   ============================================================
   Un anillo que pulsa alrededor de la burbuja para llamar
   la atención del usuario. Se oculta cuando el chat está abierto.
   ============================================================ */

.chatbot-pulse {
  position: fixed;
  bottom: 25px;
  right: 25px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 2px solid var(--accent);
  z-index: 9998;
  animation: chatbot-pulse 2s ease-out infinite;
  pointer-events: none;
}

@keyframes chatbot-pulse {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.8); opacity: 0; }
}

/* ============================================================
   PANEL DE CHAT
   ============================================================
   Es la "ventana" que se abre arriba de la burbuja.
   Contiene: header (con nombre y avatar), zona de mensajes,
   campo de entrada y pie de página.
   ============================================================ */

.chatbot-panel {
  position: fixed;
  bottom: 95px;
  right: 25px;
  width: 380px;
  max-height: 550px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 12px 50px rgba(0, 0, 0, 0.5);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  opacity: 0;
  transform: translateY(20px) scale(0.95);
  pointer-events: none;
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.chatbot-panel.abierto {
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}

/* ============================================================
   HEADER DEL PANEL
   ============================================================ */

.chatbot-header {
  background: var(--card);
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 12px;
}

.chatbot-header-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chatbot-header-avatar svg {
  width: 20px;
  height: 20px;
  fill: var(--bg);
}

.chatbot-header-info h4 {
  font-size: 14px;
  color: var(--fg);
  margin: 0;
  font-weight: 600;
}

.chatbot-header-info p {
  font-size: 11px;
  color: var(--accent);
  margin: 2px 0 0;
}

/* Botón de minimizar */
.chatbot-minimizar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
  margin-left: auto;
  flex-shrink: 0;
}

.chatbot-minimizar:hover {
  background: var(--accent-dim);
}

.chatbot-minimizar svg {
  width: 18px;
  height: 18px;
  fill: var(--fg);
}

/* ============================================================
   ZONA DE MENSAJES
   ============================================================ */

.chatbot-mensajes {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 380px;
  scroll-behavior: smooth;
}

.chatbot-mensajes::-webkit-scrollbar {
  width: 4px;
}

.chatbot-mensajes::-webkit-scrollbar-track {
  background: transparent;
}

.chatbot-mensajes::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
}

/* ============================================================
   MENSAJES INDIVIDUALES
   ============================================================ */

.chatbot-msg {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.5;
  animation: chatbot-msg-in 0.3s ease;
}

@keyframes chatbot-msg-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Mensaje del BOT */
.chatbot-msg.bot {
  background: var(--card);
  color: var(--fg);
  border: 1px solid var(--border);
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}

/* ============================================================
   TEXTO FORMATEADO DENTRO DE MENSAJES DEL BOT
   ============================================================
   Estilos para el HTML generado por parseMarkdown():
   negrita, cursiva, listas, código inline, enlaces.
   ============================================================ */

.chatbot-msg.bot p {
  margin: 0 0 8px 0;
}

.chatbot-msg.bot p:last-child {
  margin-bottom: 0;
}

.chatbot-msg.bot strong {
  color: var(--accent);
  font-weight: 600;
}

.chatbot-msg.bot em {
  font-style: italic;
  opacity: 0.9;
}

.chatbot-msg.bot ul {
  margin: 6px 0;
  padding-left: 18px;
  list-style: none;
}

.chatbot-msg.bot li {
  position: relative;
  margin: 3px 0;
  padding-left: 12px;
}

.chatbot-msg.bot li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--accent);
  font-weight: bold;
}

.chatbot-msg.bot code {
  background: rgba(0, 212, 170, 0.1);
  color: var(--accent);
  padding: 1px 5px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.chatbot-msg.bot a {
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.chatbot-msg.bot a:hover {
  opacity: 0.8;
}

/* Mensaje del USUARIO */
.chatbot-msg.usuario {
  background: var(--accent);
  color: var(--bg);
  align-self: flex-end;
  border-bottom-right-radius: 4px;
}

/* Mensaje de ERROR */
.chatbot-msg.error {
  background: rgba(255, 80, 80, 0.1);
  color: #ff6b6b;
  border: 1px solid rgba(255, 80, 80, 0.2);
  align-self: flex-start;
  font-size: 12px;
}

/* ============================================================
   INDICADOR "ESCRIBIENDO..."
   ============================================================ */

.chatbot-typing {
  display: flex;
  gap: 5px;
  align-items: center;
  padding: 14px 18px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  border-bottom-left-radius: 4px;
  align-self: flex-start;
}

.chatbot-typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--muted);
  animation: chatbot-bounce 1.2s ease-in-out infinite;
}

.chatbot-typing span:nth-child(2) { animation-delay: 0.15s; }
.chatbot-typing span:nth-child(3) { animation-delay: 0.3s; }

@keyframes chatbot-bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

/* ============================================================
   ÁREA DE ENTRADA (input + botón enviar)
   ============================================================ */

.chatbot-input-area {
  padding: 14px 16px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 10px;
  background: var(--card);
}

.chatbot-input {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 11px 14px;
  color: var(--fg);
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.chatbot-input::placeholder {
  color: var(--muted);
}

.chatbot-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-dim);
}

.chatbot-enviar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--accent);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s, transform 0.2s;
  flex-shrink: 0;
}

.chatbot-enviar:hover {
  background: #00f5c4;
  transform: scale(1.05);
}

.chatbot-enviar:active {
  transform: scale(0.95);
}

.chatbot-enviar:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.chatbot-enviar svg {
  width: 18px;
  height: 18px;
  fill: var(--bg);
}

/* ============================================================
   PIE DEL PANEL
   ============================================================ */
.chatbot-powered {
  text-align: center;
  padding: 6px;
  font-size: 9px;
  color: var(--muted);
  opacity: 0.5;
  border-top: 1px solid var(--border);
}

/* ============================================================
   DISEÑO RESPONSIVE (MÓVIL)
   ============================================================ */

@media (max-width: 480px) {
  .chatbot-panel {
    right: 10px;
    bottom: 85px;
    left: 10px;
    width: auto;
    max-height: 70vh;
  }

  .chatbot-burbuja {
    bottom: 15px;
    right: 15px;
    width: 52px;
    height: 52px;
  }

  .chatbot-pulse {
    bottom: 15px;
    right: 15px;
    width: 52px;
    height: 52px;
  }

  .chatbot-burbuja svg {
    width: 24px;
    height: 24px;
  }
}
```

### Variables CSS necesarias

Tu CSS principal (`styles.css`) debe definir estas variables. Si ya las tienes,
perfecto. Si no, añade esto al principio de tu `styles.css`:

```css
/* ============================================================
   VARIABLES CSS PARA EL TEMA OSCUR (necesarias para el chatbot)
   ============================================================ */
:root {
  /* Color de fondo principal (muy oscuro) */
  --bg: #0d1117;

  /* Color de fondo secundario (para paneles, cards) */
  --bg-secondary: #161b22;

  /* Color del texto principal */
  --fg: #e6edf3;

  /* Color apagado (para placeholders, textos secundarios) */
  --muted: #8b949e;

  /* Color accent principal (el verde-azulado de AIDA) */
  --accent: #00d4aa;

  /* Versión más oscura del accent (para hover, focus) */
  --accent-dim: rgba(0, 212, 170, 0.15);

  /* Fondo de tarjetas */
  --card: #1c2128;

  /* Color de bordes */
  --border: #30363d;
}
```

---

## 10. Paso 8: El JavaScript — Lógica del chatbot

Crea el archivo `js/chatbot.js` con este contenido **comentado línea por línea**:

```javascript
// ============================================================
// CHATBOT.JS - Lógica del widget AIDA
// ============================================================
// Este archivo crea y gestiona todo el chatbot:
//   1. La burbuja flotante
//   2. El panel de chat
//   3. El envío de mensajes a la API de Gemini (a través del proxy)
//   4. La visualización de respuestas
//   5. El registro de preguntas (logging) con IP del usuario
//   6. Parseo de markdown para respuestas con formato
//   7. Mensaje amigable cuando se alcanzan los límites de la API
//
// Todo está envuelto en una IIFE (Immediately Invoked Function
// Expression) para que las variables no se contaminen con el
// resto de tu código JavaScript.
// ============================================================

(function() {

  // ============================================================
  // CONFIGURACIÓN
  // ============================================================

  // URL del Google Apps Script desplegado (el proxy).
  // ESTA ES LA URL QUE OBTUVISTE EN EL PASO 4.
  // Cámbiala por la tuya propia.
  const PROXY_URL = 'https://script.google.com/macros/s/TU_SCRIPT_ID/exec';

  // Lista de modelos de Gemini a usar, en orden de preferencia.
  // Si el primero falla, se proba el siguiente, y así sucesivamente.
  // Esto es un "fallback" (respaldo).
  //
  // IMPORTANTE: Google depreca modelos con frecuencia. Si ves errores
  // de "modelo no disponible", consulta la lista actualizada en:
  // https://ai.google.dev/gemini-api/docs/models
  //
  // Modelos recomendados (agosto 2026):
  // - gemini-3.6-flash: más reciente, buen balance
  // - gemini-3.5-flash: alternativa estable
  // - gemini-1.5-flash: respaldo con alta cuota gratuita
  const MODELS = [
    'gemini-3.6-flash',    // Modelo principal
    'gemini-3.5-flash',    // Respaldo 1
    'gemini-1.5-flash'     // Respaldo 2
  ];

  // Índice del modelo actual (empieza por el primero de la lista).
  // Si falla, se incrementa para probar el siguiente.
  let modeloActual = 0;


  // ============================================================
  // SYSTEM PROMPT (Personalidad del chatbot)
  // ============================================================
  // Este es el "cerebro" del chatbot. Define:
  //   - Quién es (nombre, función)
  //   - Cómo se comporta (reglas)
  //   - Qué hacer en situaciones específicas
  //
  // IMPORTANTE: Cuantas más reglas le des, mejor funcionará.
  // Piensa en todas las preguntas que te podrían hacer y define
  // cómo debe responder el bot en cada caso.
  //
  // Las reglas se escriben como bullet points con "- Si...".
  // ============================================================

  const SYSTEM_PROMPT = `
    Eres AIDA, el asistente personal con Inteligencia Artificial de [TU NOMBRE].

    Tu función principal es atender a reclutadores, responsables de RRHH y
    cualquier persona interesada en tu perfil profesional.

    Reglas de comportamiento:
    - Responde SIEMPRE en español.
    - Sé profesional, cercana y proactiva.
    - Presenta la información de forma atractiva y orientada a la empresa.
    - Cuando pregunten por habilidades o experiencia, destaca cómo puedes
      aportar valor al equipo.
    - Si te preguntan por disponibilidad, indica que actualmente estás
      trabajando y que la incorporación se puede negociar en una entrevista.
    - Si te preguntan por datos de contacto, da solo el teléfono y el email.
      También sugiere el formulario de contacto de la web.
    - Si la pregunta no tiene relación con tu perfil profesional, indica
      amablemente que solo puedes proporcionar información sobre ti.
    - NUNCA inventes información que no esté en el CV.
    - Puedes resumir, comparar o estructurar la información según te pidan.
    - Si te solicitan el CV completo, sugiere descargar el PDF desde la web.
    - NUNCA te presentes al inicio de cada respuesta. Simplemente responde.
    - Si te preguntan por ti (cómo funcionas, tu tecnología), di que te
      sientes halagada, pero que tu objetivo es hablar sobre tu creador,
      y que para detalles técnicos estaría encantado de explicárselo
      en una entrevista personal.
  `;


  // ============================================================
  // BASE DE CONOCIMIENTO (El CV / información)
  // ============================================================
  // Aquí es donde metes TODA la información que el chatbot debe
  // conocer. Puede ser tu CV, datos de tu empresa, catálogo de
  // productos, etc.
  //
  // IMPORTANTE: El chatbot SOLO sabrá lo que le pongas aquí.
  // Si alguien pregunta algo que no está en esta variable, el
  // bot inventará una respuesta (o responderá que no sabe).
  //
  // Consejo: Estructura la información con títulos en mayúsculas
  // y guiones para que la IA la interprete mejor.
  // ============================================================

  const KNOWLEDGE = `
    DATOS PERSONALES:
    - Nombre: [Tu nombre completo]
    - Teléfono: [Tu teléfono]
    - Email: [Tu email]
    - Localidad: [Tu ciudad]
    - LinkedIn: [Tu URL de LinkedIn]
    - GitHub: [Tu URL de GitHub]
    - Portfolio: [Tu URL de portfolio]

    PERFIL PROFESIONAL:
    [Aquí una descripción breve de quién eres y qué buscas.
    Ejemplo: "He finalizado el grado superior en Diseño de
    Aplicaciones Web. Actualmente me estoy autoformando en
    Inteligencia Artificial y programación con Python..."]

    ENSEÑANZA REGLADA:
    - [Año]: [Título], [Centro]
    - [Año]: [Título], [Centro]

    EXPERIENCIA LABORAL:
    - [Periodo]: [Empresa], [Puesto]
    - [Periodo]: [Empresa], [Puesto]

    FORMACIÓN ONLINE:
    - [Año]: [Curso], [Plataforma], [Horas]

    HABILIDADES:
    - Tecnologías: [lista]
    - Herramientas: [lista]
    - Otros: [lista]
  `;


  // ============================================================
  // ESTADO DEL CHAT
  // ============================================================

  // Array que guarda todo el historial de mensajes de la conversación.
  // Cada mensaje tiene la forma: { role: 'user'|'assistant', content: '...' }
  // Esto permite que la IA recuerde lo que se ha dicho antes.
  let mensajes = [];

  // Flag para evitar que se envíen múltiples mensajes a la vez.
  let esperando = false;

  // IP del usuario (se obtiene una sola vez y se cachea).
  let userIP = '';


  // ============================================================
  // OBTENER IP DEL USUARIO
  // ============================================================
  // Usa el servicio gratuito ipify.org para obtener la IP pública
  // del visitante. Google Apps Script NO puede obtener la IP del
  // cliente (limitación conocida de Google), así que la obtenemos
  // desde el navegador y la enviamos con los datos de logging.
  //
  // La IP se obtiene una sola vez y se guarda en cache (userIP)
  // para no hacer peticiones innecesarias.
  // ============================================================

  async function obtenerIP() {
    if (userIP) return userIP;
    try {
      const res = await fetch('https://api.ipify.org?format=json');
      const data = await res.json();
      userIP = data.ip || '';
    } catch (e) {}
    return userIP;
  }


  // ============================================================
  // CREAR EL WIDGET (HTML dinámico)
  // ============================================================
  // Esta función genera TODO el HTML del chatbot dinámicamente.
  // No necesitas escribir HTML manualmente para el chatbot.
  // Todo se crea desde JavaScript e inyecta en el div #chatbot-root.
  // ============================================================

  function crearWidget() {
    // Buscar el contenedor en el HTML
    const root = document.getElementById('chatbot-root');

    // Inyectar todo el HTML del chatbot
    root.innerHTML = `
      <!-- Anillo de pulso que llama la atención -->
      <div class="chatbot-pulse" id="chatbot-pulse"></div>

      <!-- Botón burbuja (el círculo flotante) -->
      <button class="chatbot-burbuja" id="chatbot-burbuja" aria-label="Abrir chatbot">
        <!-- Avatar del bot (cambia tu imagen en img/aidaico.png) -->
        <img class="chatbot-burbuja-avatar" src="./img/aidaico.png" alt="AIDA">
        <!-- Icono de chat (se oculta cuando el panel está abierto) -->
        <svg class="icono-chat" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
        <!-- Icono de cerrar (se muestra cuando el panel está abierto) -->
        <svg class="icono-cerrar" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
      </button>

      <!-- Panel de chat (inicialmente oculto) -->
      <div class="chatbot-panel" id="chatbot-panel">

        <!-- Header del panel -->
        <div class="chatbot-header">
          <div class="chatbot-header-avatar">
            <img src="./img/aidaico.png" alt="AIDA" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">
          </div>
          <div class="chatbot-header-info">
            <h4>AIDA</h4>                    <!-- Nombre del bot -->
            <p>Asistente IA de [Tu nombre]</p> <!-- Descripción -->
          </div>
          <!-- Botón minimizar -->
          <button class="chatbot-minimizar" id="chatbot-minimizar" aria-label="Minimizar chat">
            <svg viewBox="0 0 24 24"><path d="M19 13H5v-2h14v2z"/></svg>
          </button>
        </div>

        <!-- Zona de mensajes (se llena dinámicamente) -->
        <div class="chatbot-mensajes" id="chatbot-mensajes">
          <!-- Mensaje de bienvenida -->
          <div class="chatbot-msg bot">
            ¡Hola! Soy AIDA, tu asistente personal con IA. Estoy aquí para
            responder todas tus preguntas sobre mi formación, experiencia y
            perfil profesional. ¿En qué puedo ayudarte?
          </div>
        </div>

        <!-- Área de entrada -->
        <div class="chatbot-input-area">
          <input type="text" class="chatbot-input" id="chatbot-input"
                 placeholder="Escribe tu pregunta..." autocomplete="off">
          <button class="chatbot-enviar" id="chatbot-enviar" aria-label="Enviar mensaje">
            <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          </button>
        </div>

        <!-- Pie del panel -->
        <div class="chatbot-powered">AIDA — Asistente IA de [Tu nombre]</div>
      </div>
    `;

    // ----------------------------------------------------------
    // EVENT LISTENERS (Escuchadores de eventos)
    // ----------------------------------------------------------

    // Cuando se hace clic en la burbuja, abrir/cerrar el panel
    document.getElementById('chatbot-burbuja').addEventListener('click', () => {
      const panel = document.getElementById('chatbot-panel');
      const abierta = panel.classList.toggle('abierto');
      document.getElementById('chatbot-burbuja').classList.toggle('abierta');
      document.getElementById('chatbot-pulse').style.display = abierta ? 'none' : 'block';
      if (abierta) document.getElementById('chatbot-input').focus();
    });

    // Cuando se hace clic en minimizar, cerrar el panel
    document.getElementById('chatbot-minimizar').addEventListener('click', () => {
      const panel = document.getElementById('chatbot-panel');
      panel.classList.remove('abierto');
      document.getElementById('chatbot-burbuja').classList.remove('abierta');
      document.getElementById('chatbot-pulse').style.display = 'block';
    });

    // Cuando se hace clic en enviar, llamar a enviarMensaje()
    document.getElementById('chatbot-enviar').addEventListener('click', () => enviarMensaje());

    // Cuando se pulsa Enter en el input, enviar el mensaje
    document.getElementById('chatbot-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        enviarMensaje();
      }
    });
  }


  // ============================================================
  // PARSEO DE MARKDOWN
  // ============================================================
  // La IA de Gemini devuelve respuestas con formato markdown
  // (asteriscos para negrita, guiones para listas, etc.).
  // Esta función convierte ese texto a HTML renderizable.
  //
  // Formatos soportados:
  //   **texto**     → <strong>texto</strong> (negrita)
  //   *texto*       → <em>texto</em> (cursiva)
  //   `codigo`      → <code>codigo</code> (código inline)
  //   - item        → <li>item</li> (listas)
  //   [texto](url)  → <a href="url">texto</a> (enlaces)
  // ============================================================

  function parseMarkdown(text) {
    let html = text
      // Negrita: **texto** → <strong>texto</strong>
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Cursiva: *texto* → <em>texto</em>
      .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
      // Código inline: `codigo` → <code>codigo</code>
      .replace(/`(.+?)`/g, '<code>$1</code>')
      // Listas con guión: - item → <li>item</li> (agrupadas en <ul>)
      .replace(/(^|\n)- (.+)/g, '$1\n<li>$2</li>')
      // Enlaces: [texto](url) → <a href="url">texto</a>
      .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      // Saltos de línea dobles → párrafos
      .replace(/\n\n/g, '</p><p>')
      // Saltos de línea simples → <br>
      .replace(/\n/g, '<br>');

    // Envolver listas consecutivas en <ul>
    html = html.replace(/(<li>.*?<\/li>(<br>)?)+/g, (match) => {
      return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
    });

    return '<p>' + html + '</p>';
  }


  // ============================================================
  // FUNCIONES DE UTILIDAD (UI)
  // ============================================================

  // ----------------------------------------------------------
  // agregarMensaje(texto, tipo)
  // ----------------------------------------------------------
  // Añade un mensaje visible en la zona de chat.
  // Para mensajes del bot, parsea el markdown a HTML.
  // Para mensajes del usuario, usa textContent (sin formato).
  //
  // Parámetros:
  //   texto - El contenido del mensaje
  //   tipo  - 'bot' | 'usuario' | 'error'
  // ----------------------------------------------------------
  function agregarMensaje(texto, tipo) {
    const contenedor = document.getElementById('chatbot-mensajes');
    const msg = document.createElement('div');
    msg.className = `chatbot-msg ${tipo}`;
    if (tipo === 'bot') {
      // Los mensajes del bot se parsean de markdown a HTML
      msg.innerHTML = parseMarkdown(texto);
    } else {
      // Los mensajes del usuario se muestran como texto plano (seguridad)
      msg.textContent = texto;
    }
    contenedor.appendChild(msg);
    contenedor.scrollTop = contenedor.scrollHeight;
  }

  // ----------------------------------------------------------
  // mostrarTyping()
  // ----------------------------------------------------------
  // Muestra el indicador de "escribiendo..." (tres puntitos).
  // ----------------------------------------------------------
  function mostrarTyping() {
    const contenedor = document.getElementById('chatbot-mensajes');
    const typing = document.createElement('div');
    typing.className = 'chatbot-typing';
    typing.id = 'chatbot-typing';
    typing.innerHTML = '<span></span><span></span><span></span>';
    contenedor.appendChild(typing);
    contenedor.scrollTop = contenedor.scrollHeight;
  }

  // ----------------------------------------------------------
  // ocultarTyping()
  // ----------------------------------------------------------
  // Elimina el indicador de "escribiendo...".
  // ----------------------------------------------------------
  function ocultarTyping() {
    const typing = document.getElementById('chatbot-typing');
    if (typing) typing.remove();
  }


  // ============================================================
  // LOGGING (Registro de preguntas con IP)
  // ============================================================
  // Envía cada pregunta, respuesta e IP al Google Apps Script
  // para que las guarde en un Google Sheet.
  //
  // La IP se obtiene del servicio ipify.org (gratuito) porque
  // Google Apps Script no permite obtener la IP del cliente.
  // ============================================================

  async function logPregunta(pregunta, respuesta) {
    if (!PROXY_URL) return;
    try {
      const ip = await obtenerIP();
      fetch(PROXY_URL, {
        method: 'POST',
        mode: 'no-cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'log',
          pregunta: pregunta,
          respuesta: respuesta,
          modelo: MODELS[modeloActual],
          url: window.location.href,
          ip: ip
        })
      });
    } catch (err) {}
  }


  // ============================================================
  // LLAMADA A LA API (a través del proxy)
  // ============================================================
  // Esta función se comunica con Google Gemini a través del proxy.
  //
  // Flujo:
  //   1. Construye el contexto (system prompt + knowledge)
  //   2. Convierte el historial de mensajes al formato de Gemini
  //   3. Envía todo al proxy
  //   4. Recibe la respuesta
  //   5. Si falla por límites de cuota, intenta con el siguiente modelo
  // ============================================================

  async function llamarAPI() {
    const modelo = MODELS[modeloActual];

    // Construir el "contexto" completo: reglas del bot + información del CV
    const contexto = SYSTEM_PROMPT +
      '\n\n=== INFORMACIÓN DEL CURRICULUM ===\n\n' +
      KNOWLEDGE +
      '\n\n=== FIN INFORMACIÓN ===\n\n' +
      'Basándote EXCLUSIVAMENTE en la información anterior, ' +
      'responde a la pregunta del usuario.';

    // Convertir el historial al formato que espera Gemini
    const contents = mensajes.map(m => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }]
    }));

    // Enviar la petición al proxy
    const response = await fetch(PROXY_URL, {
      method: 'POST',
      redirect: 'follow',
      headers: { 'Content-Type': 'text/plain' },
      body: JSON.stringify({
        action: 'chat',
        model: modelo,
        messages: contents,
        systemInstruction: { parts: [{ text: contexto }] },
        generationConfig: { temperature: 0.7, maxOutputTokens: 1024 }
      })
    });

    const text = await response.text();
    console.log('AIDA proxy response:', text);
    const result = JSON.parse(text);

    // Si hay error, intentar con el siguiente modelo (fallback)
    if (!result.ok) {
      const msg = result.error || '';
      const esLimite = /quota|rate.?limit|RESOURCE_EXHAUSTED|429|exceeded|limit/i.test(msg);
      if (esLimite && modeloActual < MODELS.length - 1) {
        modeloActual++;
        console.log(`AIDA: Probando ${MODELS[modeloActual]}...`);
        return llamarAPI();
      }
      return { error: { message: msg || 'Error al conectar con la IA' } };
    }

    return result.data;
  }


  // ============================================================
  // ENVIAR MENSAJE (Función principal)
  // ============================================================
  // Coordina todo el flujo cuando el usuario envía un mensaje:
  //   1. Lee el texto del input
  //   2. Lo añade al chat y al historial
  //   3. Muestra "escribiendo..."
  //   4. Llama a la API
  //   5. Muestra la respuesta (formateada con markdown)
  //   6. Registra la pregunta y la IP (logging)
  //   7. Si hay límites de cuota, muestra mensaje amigable
  // ============================================================

  async function enviarMensaje() {
    if (esperando) return;

    const input = document.getElementById('chatbot-input');
    const texto = input.value.trim();
    if (!texto) return;

    input.value = '';
    agregarMensaje(texto, 'usuario');
    mensajes.push({ role: 'user', content: texto });

    esperando = true;
    document.getElementById('chatbot-enviar').disabled = true;
    mostrarTyping();

    try {
      const data = await llamarAPI();
      ocultarTyping();

      if (data.error) {
        const msg = data.error.message || '';
        // Detectar si es error de límites de cuota
        const esLimite = /quota|rate.?limit|RESOURCE_EXHAUSTED|429|exceeded|limit/i.test(msg);
        if (esLimite) {
          // Mensaje amigable cuando se alcanzan los límites
          agregarMensaje(
            'Lo siento, pero Valentín tiene el chat limitado a un número de ' +
            'respuestas al día. Se ve que hoy he recibido muchas peticiones, ' +
            'lo cual me agrada porque significa que Valentín y yo despertamos ' +
            'interés. Pero me temo que tendrás que volver mañana o intentarlo ' +
            'en unas horas. Mientras tanto, puedes contactar con Valentín ' +
            'directamente a través del formulario de contacto.',
            'bot'
          );
        } else {
          agregarMensaje(`Error: ${msg || 'Error al conectar con la IA'}`, 'error');
        }
      } else {
        const respuesta = data.candidates?.[0]?.content?.parts?.[0]?.text;
        if (respuesta) {
          agregarMensaje(respuesta, 'bot');
          mensajes.push({ role: 'assistant', content: respuesta });
          logPregunta(texto, respuesta);
        } else {
          agregarMensaje('No pude generar una respuesta. Inténtalo de nuevo.', 'error');
        }
      }
    } catch (e) {
      ocultarTyping();
      agregarMensaje('Error de conexión. Comprueba tu internet.', 'error');
    }

    esperando = false;
    document.getElementById('chatbot-enviar').disabled = false;
    document.getElementById('chatbot-input').focus();
  }


  // ============================================================
  // INICIALIZACIÓN
  // ============================================================
  // Cuando el HTML esté completamente cargado, crear el widget.
  // ============================================================

  document.addEventListener('DOMContentLoaded', () => {
    crearWidget();
  });

})();
```

> **NOTA:** Si al copiar el código ves que falta algo, revisa que no se haya
> cortado ninguna línea. El archivo completo tiene ~350 líneas.

---

## 11. Paso 9: Logging de preguntas en Google Sheets (opcional)

Si quieres ver qué preguntan los visitantes de tu web, puedes configurar un
Google Sheet donde se registren todas las conversaciones, incluyendo la IP.

### 11.1 Crear el Google Sheet

1. Ve a **https://sheets.google.com** y crea una hoja nueva
2. En la primera fila, añade estas cabeceras:
   - A1: `Fecha`
   - B1: `Pregunta`
   - C1: `Respuesta`
   - D1: `Modelo`
   - E1: `URL`
   - F1: `IP`
3. Copia el **Spreadsheet ID** de la URL. Es la parte que está entre `/d/` y `/edit`:
   ```
   https://docs.google.com/spreadsheets/d/ESTO_ES_EL_SPREADSHEET_ID/edit
   ```

### 11.2 Configurar en Google Apps Script

1. Ve a tu Google Apps Script
2. **File > Project settings > Script properties**
3. Añade una nueva propiedad:

| Propiedad | Valor |
|-----------|-------|
| `SPREADSHEET_ID` | `El ID que copiaste` |

4. Guarda y **despliega una nueva versión** (Deploy > Manage deployments > Edit)

### 11.3 Verificar permisos del Sheet

1. Abre tu Google Sheet
2. Haz clic en **"Compartir"** (arriba a la derecha)
3. Añade el email de tu cuenta de Google (la misma del Script)
4. Dale permisos de **"Editor"**
5. Envía

### 11.4 Ver las preguntas

Cada vez que alguien use el chatbot, se guardará una fila en el Sheet con:
- Fecha y hora de la pregunta
- Qué preguntó
- Cómo respondió el bot
- Qué modelo de Gemini se usó
- En qué página de tu web se hizo la pregunta
- **IP del usuario** (obtenida vía ipify.org)

### 11.5 Obtener la IP del usuario

La IP se obtiene automáticamente desde el navegador usando el servicio
gratuito **ipify.org**. Google Apps Script no puede obtener la IP del
cliente (limitación conocida de Google), así que el chatbot la obtiene
antes de enviar el log y la incluye en los datos.

---

## 12. Personalización

### Cambiar el nombre del bot

Busca y reemplaza "AIDA" por el nombre que quieras en:
1. `js/chatbot.js` — Línea del `SYSTEM_PROMPT` (donde dice "Eres AIDA...")
2. `js/chatbot.js` — Dentro de `crearWidget()` (el `<h4>AIDA</h4>` y la descripción)
3. `js/chatbot.js` — El mensaje de bienvenida
4. `css/chatbot.css` — Solo si quieres cambiar estilos específicos del nombre

### Cambiar el avatar

Sustituye la imagen `img/aidaico.png` por la tuya. Recomendaciones:
- Formato: PNG o JPG
- Tamaño: al menos 60x60 píxeles
- Forma: cuadrada (se recorta a círculo con CSS)

### Cambiar los colores

Modifica las variables CSS en tu archivo `styles.css`:

```css
:root {
  --accent: #00d4aa;        /* Color principal (burbuja, botones) */
  --accent-dim: rgba(0, 212, 170, 0.15); /* Versión transparente */
  --bg: #0d1117;            /* Fondo de la página */
  --bg-secondary: #161b22;  /* Fondo del panel de chat */
  --fg: #e6edf3;            /* Color del texto */
  --muted: #8b949e;         /* Texto apagado */
  --card: #1c2128;          /* Fondo de tarjetas/header */
  --border: #30363d;        /* Color de bordes */
}
```

Algunos colores predefinidos que te gustarán:
- **Verde azulado (actual):** `#00d4aa`
- **Azul:** `#3b82f6`
- **Púrpura:** `#8b5cf6`
- **Naranja:** `#f59e0b`
- **Rosa:** `#ec4899`

### Cambiar el SYSTEM_PROMPT (personalidad)

Edita el texto dentro de `const SYSTEM_PROMPT = \`...\`` en `chatbot.js`.
Cada línea que empieza por "- Si..." es una regla. Puedes:
- Añadir nuevas reglas
- Modificar las existentes
- Cambiar el tono (más formal, más casual, etc.)

### Cambiar la base de conocimiento

Edita el texto dentro de `const KNOWLEDGE = \`...\`` en `chatbot.js`.
Puedes meter toda la información que quieras: CV, catálogo de productos,
preguntas frecuentes, etc.

### Cambiar los modelos de Gemini

Edita el array `MODELS` en `chatbot.js`:
```javascript
const MODELS = [
  'gemini-3.6-flash',    // Tu modelo principal
  'gemini-3.5-flash',    // Respaldo
  'gemini-1.5-flash'     // Último respaldo
];
```

Consulta los modelos disponibles en: https://ai.google.dev/gemini-api/docs/models

> **IMPORTANTE:** Google depreca modelos con frecuencia. Si ves errores de
> "modelo no disponible", consulta la página anterior para ver los modelos actuales.

### Formato de las respuestas (Markdown)

El chatbot parsea automáticamente markdown en las respuestas del bot:

| Markdown | Resultado visual |
|---|---|
| `**texto**` | **texto** (negrita en color accent) |
| `*texto*` | *texto* (cursiva) |
| `` `código` `` | `código` (fondo transparente) |
| `- item1` | • item1 (lista con viñetas) |
| `[texto](url)` | texto (enlace clickeable) |

Los mensajes del usuario se muestran siempre como texto plano (por seguridad).

### Mensaje de límites de cuota

Cuando se alcanzan los límites de la API, el chatbot muestra un mensaje
amigable en lugar de un error técnico. Puedes personalizarlo buscando
la cadena `'Lo siento, pero Valentín tiene el chat limitado...'` en
`chatbot.js` y modificándola.

---

## 13. Solución de problemas

### "Error de conexión. Comprueba tu internet."

**Causa más común:** El Google Apps Script no está desplegado correctamente.

Soluciones:
1. Verifica que la URL en `PROXY_URL` (chatbot.js) es correcta
2. Ve a Google Apps Script > Deploy > Manage deployments y comprueba que hay un despliegue activo
3. Si cambiaste el código, crea una **nueva versión** del despliegue
4. Abre la URL del proxy en el navegador — debería decir "AIDA Proxy activo"
5. Mira la consola del navegador (F12 > Console) para ver el error exacto

### "No tienes permiso para llamar a UrlFetchApp.fetch"

**Causa:** El Script no tiene permiso para hacer peticiones HTTP externas.

Solución:
1. En el editor de Google Apps Script, selecciona la función `proxyGemini`
2. Haz clic en **Run** (Ejecutar)
3. Si pide autorización, autorízala
4. Vuelve a desplegar una nueva versión

### "This model is no longer available"

**Causa:** El nombre del modelo de Gemini ha cambiado o ya no existe.

Solución:
1. Ve a https://ai.google.dev/gemini-api/docs/models
2. Busca los nombres actuales de los modelos
3. Actualiza el array `MODELS` en `chatbot.js`
4. Actualiza el modelo por defecto en `google-apps-script.gs`

### "GEMINI_API_KEY no configurada en Script Properties"

**Causa:** No has guardado la API Key en las propiedades del Script.

Solución:
1. Google Apps Script > File > Project settings
2. Script properties > Add script property
3. Nombre: `GEMINI_API_KEY`, Valor: tu API Key
4. Despliega una nueva versión

### El chatbot no aparece en la web

**Causas posibles:**
1. No has añadido `<div id="chatbot-root"></div>` al HTML
2. No has incluido `<script src="./js/chatbot.js" defer></script>`
3. El archivo `chatbot.js` no está en la ruta correcta
4. Hay un error de JavaScript que impide la carga

Solución: Abre la consola del navegador (F12 > Console) y busca errores en rojo.

### El chatbot se ve sin estilos (todo en negro y descolocado)

**Causa:** No se está cargando el CSS del chatbot.

Solución: Verifica que en el `<head>` tienes:
```html
<link rel="stylesheet" href="./css/chatbot.css">
```

### Los colores no se ven bien

**Causa:** Las variables CSS (`--accent`, `--bg`, etc.) no están definidas.

Solución: Añade las variables en tu `styles.css` (consulta la sección de Personalización).

### El logging no graba en el Google Sheet

**Causas posibles:**
1. No has configurado `SPREADSHEET_ID` en Script Properties
2. El Google Sheet no tiene compartido el acceso con tu cuenta de Google
3. No has desplegado una nueva versión después de cambiar el código

Solución:
1. Verifica `SPREADSHEET_ID` en Script Properties
2. Comparte el Sheet con tu email de Google como Editor
3. Despliega una nueva versión

---

## Enhorabuena

Si has llegado hasta aquí, ya tienes tu chatbot con IA funcionando en tu web.
Si tienes dudas, revisa la sección de solución de problemas o busca en Google
"Google Apps Script [tu error]".

---

*Documento creado como guía paso a paso para la creación del chatbot AIDA.*
*Última actualización: Agosto 2026.*
