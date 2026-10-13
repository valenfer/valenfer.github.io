# Motor de cuatro tiempos

Recreación interactiva tipo Anatomy para entender el ciclo de un motor de cuatro tiempos.

## Controles

- Arrastra el control de posición para mover el pistón.
- Cambia las RPM para modificar la velocidad de reproducción.
- Usa `Reproducir` y `Pausar`.
- Salta directamente a admisión, compresión, explosión o escape.
- Usa las flechas izquierda/derecha para avanzar o retroceder manualmente.
- Usa la barra espaciadora para reproducir o pausar.

Las lecturas de presión y temperatura son aproximaciones didácticas, no datos de calibración de un motor real.

## Ejecución local

Desde la raíz de `valenfer.github.io`:

```bash
python -m http.server 4173
```

Abre `http://127.0.0.1:4173/recreaciones/motor-cuatro-tiempos/`.

## Verificación rápida

```bash
node --check /ruta/al/script-extraido.js
curl -I http://127.0.0.1:4173/recreaciones/motor-cuatro-tiempos/
```
