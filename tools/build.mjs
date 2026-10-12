// Convierte el Index.html de Apps Script en el index.html de GitHub Pages.
//
//   node tools/build.mjs <ruta/al/Index.html> [commit]
//
// Solo cambia la cabecera: quita <base target="_top"> (hacía falta dentro del
// iframe de Google), agrega título, viewport, íconos y manifest (que dentro de
// Apps Script no funcionaban) y carga config.js, demo.js y api.js antes que la
// app. El resto del archivo queda idéntico. Si la cabecera del original cambia
// y algo no se encuentra, falla en vez de publicar una página a medias.
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

const [src, commit = ''] = process.argv.slice(2);
if (!src) { console.error('uso: node tools/build.mjs <Index.html> [commit]'); process.exit(2); }
let html = readFileSync(src, 'utf8');

function replaceOnce(re, to, what) {
  const hits = html.match(new RegExp(re.source, re.flags.includes('g') ? re.flags : re.flags + 'g')) || [];
  if (hits.length !== 1) { console.error(`build: esperaba 1 "${what}", encontré ${hits.length}`); process.exit(1); }
  html = html.replace(re, to);
}

// GitHub Pages deja que el navegador guarde cada archivo 10 minutos. Con la
// huella del contenido en el link, un cambio en config.js o api.js se ve en
// cuanto llega el index.html nuevo. Por eso index.html se regenera después
// de tocar cualquiera de esos archivos.
const hashOf = f => createHash('sha256').update(readFileSync(new URL('../' + f, import.meta.url))).digest('hex').slice(0, 10);

// La versión más alta que menciona el archivo (los comentarios marcan "v2.15").
const version = [...html.matchAll(/\bv(\d+)\.(\d+)\b/g)]
  .map(m => [Number(m[1]), Number(m[2])])
  .sort((a, b) => b[0] - a[0] || b[1] - a[1])
  .map(([a, b]) => `${a}.${b}`)[0] || '';
const build = JSON.stringify({ version, commit: commit.slice(0, 7) });

replaceOnce(/[ \t]*<base target="_top">\r?\n/, '', '<base target="_top">');
replaceOnce(/<!-- No icon\/manifest links here on purpose\.[\s\S]*?-->/, [
  '<title>Union Arena Tracker</title>',
  '  <meta name="viewport" content="width=device-width, initial-scale=1">',
  '  <meta name="theme-color" content="#0e0d13">',
  '  <meta name="apple-mobile-web-app-capable" content="yes">',
  '  <meta name="mobile-web-app-capable" content="yes">',
  '  <meta name="apple-mobile-web-app-title" content="UA Tracker">',
  '  <meta name="apple-mobile-web-app-status-bar-style" content="black">',
  '  <link rel="icon" type="image/png" href="icons/favicon.png">',
  '  <link rel="apple-touch-icon" href="icons/apple-touch-icon.png">',
  '  <link rel="manifest" href="manifest.webmanifest">',
  // Dentro de Apps Script el fondo lo ponía el iframe; aquí el degradado del
  // body se repetía debajo de pantallas cortas (una franja visible).
  '  <style>html { background: #0e0d13; }</style>',
  `  <script>window.UAT_BUILD = ${build};</script>`,
  `  <script src="config.js?v=${hashOf('config.js')}"></script>`,
  `  <script src="demo.js?v=${hashOf('demo.js')}"></script>`,
  `  <script src="api.js?v=${hashOf('api.js')}"></script>`,
].join('\n'), 'comentario de íconos');

const banner = `<!-- GENERADO por tools/build.mjs desde Index.html${commit ? ' @ ' + commit.slice(0, 7) : ''}. No editar aquí: los cambios se hacen en el repo privado. -->\n`;
writeFileSync('index.html', html.replace(/^<!DOCTYPE html>\r?\n/i, m => m + banner));
console.log(`index.html listo (v${version}${commit ? ', ' + commit.slice(0, 7) : ''}, ${html.length} bytes)`);
