# AstroAIDA

Sitio estático de astronomía para observación desde Sevilla (`37.38283, -5.97317`, 0 m),
publicable bajo `/astroaida/` en GitHub Pages.

- **Frontend:** HTML/CSS/JS plano. Solo lee JSON locales de `astroaida/data/`.
- **Backend:** recopiladores Python 3.11+ que normalizan y validan datos de
  NASA (APOD, NeoWs), AstronomyAPI, In-The-Sky (ICS), Open-Meteo y MyMemory antes de escribirlos de forma atómica.
- **Idioma de la interfaz:** español. El texto de origen de APOD se traduce
  server-side con MyMemory y se conserva el original. Las efemérides usan
  traducción astronómica controlada por reglas/glosario.

Los JSON publicados usan `status: "live"` cuando proceden de las APIs. El frontend también
admite `status: "preview"` para mostrar de forma honesta un fallback de muestra.

## Servidor local

Desde la raíz del repositorio:

```bash
python -m http.server 8000
# abre http://localhost:8000/astroaida/
```

## Pruebas y validación

Desde la raíz del repositorio:

```bash
python -m unittest discover -s astroaida/tests -v
node --test astroaida/tests/test_moon_renderer.js
python astroaida/scripts/validate_site.py
python -m py_compile astroaida/scripts/collect_data.py astroaida/scripts/validate_site.py
node --check astroaida/main.js
node --check astroaida/moon-renderer.js
```

El validador comprueba: archivos requeridos, JSON bien formado, metadatos
(`source`, `fetched_at`, `status`), estados permitidos (`preview`/`live`), URLs inseguras
(`javascript:`, `file:`, `data:`), fugas de rutas locales, secretos con forma de credencial,
links vacíos y `_blank` sin `rel="noopener"`, canonical, metadatos y contrato de efemérides
(fecha ISO, timezone, eventos con visibilidad y fuentes HTTPS).

## Recopilación de datos

Variables de entorno requeridas (nombres en `astroaida/.env.example`):

| Variable                | Descripción                                   |
| ----------------------- | --------------------------------------------- |
| `NASA_API_KEY`          | Clave de https://api.nasa.gov/ (APOD y NeoWs) |
| `ASTRONOMY_APP_ID`      | App ID de AstronomyAPI                        |
| `ASTRONOMY_APP_SECRET`  | App secret de AstronomyAPI                    |

Comandos:

```bash
# Modo fixtures: escribe los seis JSON de muestra (sin red, sin credenciales)
python astroaida/scripts/collect_data.py --fixtures

# Modo en vivo: descarga, normaliza, valida y escribe (requiere credenciales)
NASA_API_KEY=... ASTRONOMY_APP_ID=... ASTRONOMY_APP_SECRET=... \
  python astroaida/scripts/collect_data.py

# Dry-run: descarga y valida sin escribir
NASA_API_KEY=... ASTRONOMY_APP_ID=... ASTRONOMY_APP_SECRET=... \
  python astroaida/scripts/collect_data.py --dry-run
```

Comportamiento de fallo: si una fuente no puede refrescarse, el script conserva el
último conjunto válido, avisa y termina con código distinto de cero. Solo se escribe un
archivo tras superar la validación de esquema (escritura atómica vía `os.replace`).
No se registran cabeceras de autorización ni claves en los logs.

### Programación diaria

El workflow `Actualizar datos de AstroAIDA` está pensado para construir los JSON
del **día siguiente** justo antes de medianoche en Sevilla:

- Hora funcional: **23:59 Europe/Madrid**.
- Regla de fecha: si hoy es día 15 en Sevilla, esa ejecución genera y publica
  `target_date = 16` para que durante el día 16 la página muestre los datos de ese día.
- GitHub Actions solo admite cron en UTC, así que el workflow se dispara a las
  dos equivalencias posibles (`21:59 UTC` y `22:59 UTC`) y una guarda interna
  permite continuar únicamente cuando la hora local real de Sevilla es `23:59`.
  Esto evita publicar la fecha equivocada durante cambios CET/CEST.

### Fuentes de datos

| Fuente | Uso | Datos |
| ------ | --- | ----- |
| NASA APOD | Imagen/vídeo astronómico del día | Título, explicación, media |
| NASA NeoWs | Asteroides cercanos a la Tierra | Posiciones, diámetros, velocidad |
| AstronomyAPI | Posiciones de cuerpos, fase lunar, carta celeste | Coordenadas, fase, imagen |
| In-The-Sky | Efemérides astronómicas (anuario ICS) | Eventos, fechas, descripciones |
| Open-Meteo | Meteorología para Sevilla | Nubosidad, visibilidad, precipitación |
| MyMemory | Traducción server-side best-effort | Títulos y descripciones en español |

### Efemérides

La sección "Efemérides" muestra eventos astronómicos relevantes para Sevilla:

- **Fuente principal:** Catálogo anual iCalendar de In-The-Sky
  (`https://in-the-sky.org/newscalyear_ical.php?year=YYYY&maxdiff=7`)
- **Cálculo local:** Astronomy Engine obtiene altura, acimut, oscuridad y los contactos
  del eclipse solar desde las coordenadas de Sevilla.
- **Eventos especiales contrastados:**
  - Eclipse solar parcial del 12 de agosto de 2026, calculado localmente y contrastado con IGN
  - Perseidas 2026, referencia editorial del IGN (máximo ~04:00-06:00 del 13 de agosto)
- **Clima:** Open-Meteo para nubosidad, visibilidad y probabilidad de precipitación
  durante las horas en que el Sol está al menos 6° bajo el horizonte
- **Traducción:** Títulos y descripciones se traducen server-side con MyMemory;
  los nombres propios y designaciones se conservan en el idioma original
- **Validación de visibilidad:** Los eventos no verifiables se marcan como
  `contextual` o `uncertain` según corresponda

El navegador solo carga `data/ephemerides.json`. No consulta proveedores externos
ni expone secretos.

## Traducción

- APOD: `title_es` y `explanation_es` se obtienen vía MyMemory (server-side)
- Efemérides: títulos breves traducidos con glosario astronómico controlado
- Si MyMemory falla, se conserva el original y se marca `translation_status: 'unavailable'`
- Atribución a MyMemory en la lista de fuentes de la sección y en el JSON

## Credenciales seguras

- Nunca incluyas claves en el código ni en el repositorio.
- En GitHub, usa **Settings → Secrets and variables → Actions** y define
  `NASA_API_KEY`, `ASTRONOMY_APP_ID` y `ASTRONOMY_APP_SECRET`.
- El workflow de actualización las inyecta como variables de entorno del runner;
  nunca llegan al navegador.

## ¿Por qué el navegador no usa las API directamente?

Las llamadas a NASA/AstronomyAPI requieren credenciales. Cualquier clave embebida en
HTML/JS sería pública, revocable y un riesgo de abuso. Por eso el navegador solo lee
JSON normalizado local, producido por el recopilador en el servidor/CI.

## Evolución posible

1. **Selector de coordenadas/observatorio**: la configuración del observador está
   centralizada (`OBSERVER_*` en `scripts/collect_data.py`) para ampliarla después.
2. **Más catálogos oficiales:** ampliar los eventos editoriales especiales sin
   degradar la comprobación geométrica local de Astronomy Engine.

## Estructura

```text
astroaida/
├── index.html
├── styles.css
├── moon-renderer.js        # renderer UMD del disco lunar (canvas, sin dependencias)
├── main.js
├── assets/favicon.svg
├── data/                  # seis JSON normalizados (muestra o en vivo)
│   ├── apod.json
│   ├── sky-today.json
│   ├── moon.json
│   ├── star-chart.json
│   ├── near-earth.json
│   └── ephemerides.json
├── scripts/
│   ├── collect_data.py    # recopilador + normalización + validación
│   └── validate_site.py   # validador estático del sitio
├── tests/                 # unittest + fixtures de API
├── requirements.txt       # astronomy-engine==2.1.19
├── .env.example
└── README.md
```
