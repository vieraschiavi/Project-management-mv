// © 2026 Martín Viera. Todos los derechos reservados.
// Empaqueta la interfaz de escritorio (React) -> desktop/ui/dist/.
//
// Autocontenido: React queda DENTRO del bundle y nada se baja de internet. No
// es una preferencia de estilo — el producto promete funcionar sin conexión y
// se instala en PCs corporativas que a veces no tienen salida a la red. Un
// solo `<script src="https://…">` lo rompería justo en esas.
//
// esbuild y no webpack/vite: son cinco archivos y un `import`. Una cadena de
// build con configuración propia sería más código de infraestructura que de
// interfaz, en un repositorio cuyo producto es Python.

import { build } from 'esbuild';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const aqui = dirname(fileURLToPath(import.meta.url));
const raizUi = join(aqui, '..', 'ui');
const salida = join(raizUi, 'dist');
mkdirSync(salida, { recursive: true });

await build({
  entryPoints: [join(raizUi, 'src', 'index.jsx')],
  bundle: true,
  minify: true,
  outfile: join(salida, 'ui.js'),
  loader: { '.jsx': 'jsx' },
  jsx: 'automatic',
  target: ['chrome120'],   // el Chromium que trae Electron 33
  define: { 'process.env.NODE_ENV': '"production"' },
  logLevel: 'info',
});

const css = readFileSync(join(raizUi, 'src', 'styles.css'), 'utf8');

// El icono de la marca, embebido como data URI desde el archivo real.
//
// Se lee en tiempo de build a propósito: así el `.ico`/`.png` de packaging/
// sigue siendo la ÚNICA fuente de verdad. Pegar un base64 a mano acá haría que
// el logo de la web y el del programa se separaran el día que uno cambie, sin
// que nada lo avise.
//
// Y va embebido en vez de como archivo suelto porque el navegador pide
// /favicon.ico SIEMPRE: sin esto queda un 404 en la consola en cada arranque,
// y en un programa que se vende un error en consola es una pregunta incómoda
// esperando a que alguien abra las herramientas de desarrollo.
function iconoEmbebido() {
  for (const ruta of [
    join(aqui, '..', '..', 'packaging', 'assets', 'icon.png'),
    join(aqui, '..', '..', 'landing', 'apple-touch-icon.png'),
  ]) {
    if (existsSync(ruta)) {
      return 'data:image/png;base64,' + readFileSync(ruta).toString('base64');
    }
  }
  // Sin icono se sigue igual: un favicon faltante no puede romper el build de
  // la interfaz. Se avisa para que no pase inadvertido.
  console.warn('  (sin icono: no encontré packaging/assets/icon.png)');
  return '';
}

const LOGO = iconoEmbebido();

// CSP estricta: sin 'unsafe-eval' y sin orígenes externos. `connect-src 'self'`
// alcanza porque la UI la sirve el MISMO servidor que la API; si algún día se
// abriera desde otro origen habría que ampliarla a mano, y que haya que
// hacerlo a mano es justamente la idea.
writeFileSync(join(salida, 'index.html'), `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'self'; img-src 'self' data:">
${LOGO ? `<link rel="icon" href="${LOGO}">` : ''}
<title>MV Project Management</title>
<style>
${css}
</style>
</head>
<body><div id="root"></div><script src="ui.js"></script></body>
</html>
`);

console.log('desktop/ui/dist listo (React empaquetado, sin CDN)');
