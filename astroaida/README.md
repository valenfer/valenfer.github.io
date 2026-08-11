# AstroAIDA

Sitio estático de astronomía para observación desde Sevilla (`37.38283, -5.97317`, 0 m),
publicable bajo `/astroaida/` en GitHub Pages.

- **Frontend:** HTML/CSS/JS plano. Solo lee JSON locales de `astroaida/data/`.
- **Backend:** recopiladores Python 3.11 (stdlib) que normalizan y validan datos de
  NASA (APOD, NeoWs) y AstronomyAPI antes de escribirlos de forma atómica.
- **Idioma de la interfaz:** español. El texto de origen de APOD se mantiene en inglés y se etiqueta.

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
python astroaida/scripts/validate_site.py
python -m py_compile astroaida/scripts/collect_data.py astroaida/scripts/validate_site.py
node --check astroaida/main.js
```

El validador comprueba: archivos requeridos, JSON bien formado, metadatos
(`source`, `fetched_at`, `status`), estados permitidos (`preview`/`live`), URLs inseguras
(`javascript:`, `file:`, `data:`), fugas de rutas locales, secretos con forma de credencial,
links vacíos y `_blank` sin `rel="noopener"`, canonical y metadatos.

## Recopilación de datos

Variables de entorno requeridas (nombres en `astroaida/.env.example`):

| Variable                | Descripción                                   |
| ----------------------- | --------------------------------------------- |
| `NASA_API_KEY`          | Clave de https://api.nasa.gov/ (APOD y NeoWs) |
| `ASTRONOMY_APP_ID`      | App ID de AstronomyAPI                        |
| `ASTRONOMY_APP_SECRET`  | App secret de AstronomyAPI                    |

Comandos:

```bash
# Modo fixtures: escribe los cinco JSON de muestra (sin red, sin credenciales)
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

El workflow `.github/workflows/update-astroaida.yml` se ejecuta dos veces al día y también
admite lanzamiento manual. Valida todo el sitio antes de hacer commit y limita la escritura
a `astroaida/data/`. Si una fuente falla, puede publicar las demás actualizaciones válidas,
conserva el fallback anterior de la fuente fallida y termina en rojo para generar una alerta.

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
2. Traducción opcional del texto editorial de APOD, conservando siempre el original.

## Estructura

```text
astroaida/
├── index.html
├── styles.css
├── main.js
├── assets/favicon.svg
├── data/                  # cinco JSON normalizados (muestra o en vivo)
│   ├── apod.json
│   ├── sky-today.json
│   ├── moon.json
│   ├── star-chart.json
│   └── near-earth.json
├── scripts/
│   ├── collect_data.py    # recopilador + normalización + validación
│   └── validate_site.py   # validador estático del sitio
├── tests/                 # unittest + fixtures de API
├── .env.example
└── README.md
```
