# CapyMatchTracker — pantallas públicas

Esta es la parte **pública** del Union Arena Tracker del equipo Capy: solo las
pantallas, publicadas con GitHub Pages. El servidor (Apps Script + Google
Sheets) y el código fuente viven en el repo privado `roxceth/UAMatchTracker`.

Aquí no hay datos, PINs ni código del servidor. Las pantallas piden todo al
Apps Script, y el servidor exige PIN y sesión para cada cosa.

## Archivos

| Archivo | Qué es |
|---|---|
| `index.html` | **Generado.** El `Index.html` del repo privado con la cabecera adaptada. No se edita aquí. |
| `api.js` | Puente: crea un `google.script.run` que por debajo llama al `/exec` del Apps Script con `fetch` (POST `text/plain`, sin preflight CORS). |
| `config.js` | El link `/exec` del Apps Script (`apiUrl`) y el de la copia de prueba (`qaApiUrl`). Vacío = modo demo. |
| `demo.js` | Datos falsos para el modo demo (los mismos del QA del repo privado). |
| `manifest.webmanifest`, `icons/` | Ícono y nombre al agregar la app a la pantalla de inicio. |
| `tools/build.mjs` | Genera `index.html` desde el `Index.html` de Apps Script. |
| `qa/qa_pages.py` | QA de esta versión (build, demo, modo QA, sesión, íconos, puente contra un `/exec` falso). |
| `qa/qa_e2e.py`, `qa/fake_exec.js` | Punta a punta: la página contra un `/exec` local que corre el `Code.gs` real del repo privado. |

## Modo demo

Sin `apiUrl` en `config.js`, o con `?demo` al final del link, la página usa
datos falsos y no llama a ningún servidor. Sirve para probar las pantallas en
cualquier teléfono o computadora. Cualquier PIN entra. Arriba aparece
"DEMO · fake data".

## Modo QA

Con `?qa` al final del link, la página usa `qaApiUrl`: el Apps Script de la
copia "Union Arena Tracker - QA" de la hoja. Arriba aparece "QA · test copy
of the sheet" en azul. El link del servidor sale siempre de `config.js`,
nunca del URL, para que nadie pueda armar un link que mande los PINs a otro
lado.

## Generar y probar

```bash
node tools/build.mjs ../uamatchtracker/Index.html $(git -C ../uamatchtracker rev-parse HEAD)
python3 qa/qa_pages.py ../uamatchtracker/Index.html
python3 qa/qa_e2e.py ../uamatchtracker      # necesita la rama con doPost (v2.16)
```
