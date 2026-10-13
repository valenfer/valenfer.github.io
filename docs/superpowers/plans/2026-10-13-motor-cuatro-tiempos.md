# Motor de cuatro tiempos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear una recreación interactiva y educativa de un motor de cuatro tiempos con pistón, RPM, fases del ciclo y lecturas dinámicas de presión y temperatura.

**Architecture:** Página estática autónoma en `recreaciones/motor-cuatro-tiempos/index.html`, con SVG inline para la máquina y JavaScript vanilla para el modelo, animación y controles. El modelo calcula una fase continua de 720 grados, posición del pistón, presión y temperatura aproximadas; todos los textos y medidores se derivan de ese mismo estado.

**Tech Stack:** HTML5, CSS3, SVG inline, JavaScript vanilla, Node.js para comprobaciones, servidor HTTP local y Playwright/Chrome disponible para verificación visual.

**Spec:** Diseño aprobado en conversación el 13 de octubre de 2026.

## Global Constraints

- No introducir dependencias externas ni CDN.
- Publicar dentro de `valenfer.github.io/recreaciones/motor-cuatro-tiempos/`.
- Mantener accesibilidad, responsive móvil y `prefers-reduced-motion`.
- Los valores de presión y temperatura son educativos y deben estar etiquetados como aproximados.
- Verificar la página real antes de hacer commit y push.

---

### Task 1: Crear la página interactiva

**Files:**
- Create: `recreaciones/motor-cuatro-tiempos/index.html`

**Interfaces:**
- `engineStateFromAngle(angle, rpm)` devuelve `{ angle, cycleAngle, phase, phaseLabel, piston, pressure, temperature, intakeOpen, exhaustOpen, ignition }`.
- `render(state)` actualiza SVG, medidores, textos, clases de fase y el panel de explicación.
- Controles HTML con IDs `pistonRange`, `rpmRange`, `playButton`, `phaseButtons`, `resetButton`.

- [ ] **Step 1: Escribir el HTML semántico y el SVG del corte del motor.**
  Incluir encabezado, panel de control, figura SVG con cilindro, culata, válvulas, bujía, cámara, pistón, biela y cigüeñal, panel de lecturas y explicación.

- [ ] **Step 2: Implementar el modelo físico educativo.**
  Normalizar el ángulo a `[0,720)`, dividirlo en admisión `0–180`, compresión `180–360`, explosión `360–540` y escape `540–720`; usar una curva cosenoidal para la posición del pistón y funciones suaves por fase para presión y temperatura.

- [ ] **Step 3: Implementar la animación y la interacción.**
  Conectar el slider del pistón al ángulo, el slider de RPM a la velocidad angular, reproducción/pausa, reinicio, botones de fase, arrastre táctil sobre el pistón y teclado. Pausar automáticamente bajo `prefers-reduced-motion`.

- [ ] **Step 4: Implementar la presentación visual.**
  Crear tema oscuro tipo banco de laboratorio, colores de gases y combustión, medidores con gradientes, estados de válvulas, partículas SVG ligeras y diseño responsive sin overflow horizontal.

- [ ] **Step 5: Añadir contenido educativo y mensajes de precisión.**
  Mostrar qué ocurre en la fase actual, qué válvula está abierta, qué sucede con la mezcla y una nota visible indicando que las lecturas son aproximaciones didácticas.

### Task 2: Verificación local y visual

**Files:**
- Modify: `recreaciones/motor-cuatro-tiempos/index.html` solo si las verificaciones detectan fallos.
- Create: `recreaciones/motor-cuatro-tiempos/README.md`

- [ ] **Step 1: Ejecutar comprobación de sintaxis JavaScript.**
  Extraer el bloque script y ejecutar `node --check`.

- [ ] **Step 2: Servir la carpeta y comprobar HTTP 200.**
  Lanzar servidor local, consultar la ruta y verificar el contenido de la página.

- [ ] **Step 3: Verificar interacción real.**
  Usar navegador automatizado para cambiar RPM, mover el pistón, pulsar reproducción y comprobar que cambian lecturas, transformación SVG y fase.

- [ ] **Step 4: Verificar escritorio y móvil.**
  Capturar/inspeccionar las vistas 1440×900 y 390×844, comprobando ausencia de overflow y controles táctiles utilizables.

- [ ] **Step 5: Documentar ejecución.**
  Añadir README con propósito, ruta, controles y comandos de verificación.

### Task 3: Commit, push y verificación remota

**Files:**
- Modify: git index and history only.

- [ ] **Step 1: Revisar diff y estado.**
  Confirmar que solo se incluyen el plan, la recreación y su README.

- [ ] **Step 2: Crear commit.**
  Usar mensaje `feat: add four-stroke engine anatomy recreation`.

- [ ] **Step 3: Subir `main` al remoto existente.**
  Ejecutar `git push origin main`.

- [ ] **Step 4: Verificar el commit remoto y la ruta publicada.**
  Leer el SHA remoto y consultar la URL de GitHub Pages con caché invalidada; confirmar que contiene el título de la recreación. Si Pages aún no ha terminado, reportar el estado exacto y reintentar antes de finalizar.
