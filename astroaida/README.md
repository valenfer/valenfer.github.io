# AstroAIDA

Sitio estático de astronomía para observación desde Sevilla (`37.38283, -5.97317`, 0 m),
publicable bajo `/astroaida/` en GitHub Pages.

- **Frontend:** HTML/CSS/JS plano. Solo lee JSON locales de `astroaida/data/`.
- **Backend:** recopiladores Python 3.11 (stdlib) que normalizan y validan datos de
  NASA (APOD, NeoWs) y AstronomyAPI antes de escribirlos de forma atómica.
- **Idioma de la interfaz:** español. El texto de origen de APOD se mantiene en inglés y se etiqueta.

> En esta fase el sitio funciona con **datos de muestra** (marcados como `status: "preview"`).
> Los recopiladores están listos, pero la recopilación en vivo requiere credenciales nuevas.

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

## Credenciales seguras

- Nunca incluyas claves en el código ni en el repositorio.
- En GitHub, usa **Settings → Secrets and variables → Actions** y define
  `NASA_API_KEY`, `ASTRONOMY_APP_ID` y `ASTRONOMY_APP_SECRET`.
- El workflow futuro las inyectará como variables de entorno del runner;
  nunca llegan al navegador.

## ¿Por qué el navegador no usa las API directamente?

Las llamadas a NASA/AstronomyAPI requieren credenciales. Cualquier clave embebida en
HTML/JS sería pública, revocable y un riesgo de abuso. Por eso el navegador solo lee
JSON normalizado local, producido por el recopilador en el servidor/CI.

## Futuro

1. **Workflow de GitHub Actions** (`update-astroaida.yml`): recopilación programada con
   credenciales nuevas como Secrets, commit de los datos validados y publicación.
2. **Selector de coordenadas/observatorio**: la configuración del observador está
   centralizada (`OBSERVER_*` en `scripts/collect_data.py`) para ampliarla después.
3. Prueba de humo real contra AstronomyAPI y generación del conjunto en vivo.

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
