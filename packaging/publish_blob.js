// Publica el instalador recién compilado en Vercel Blob, con un nombre de
// archivo FIJO (sin sufijo de versión) — así el link de descarga de la
// landing (/api/download-installer) nunca tiene que actualizarse entre
// releases: cada build exitoso pisa el mismo blob con la versión más nueva.
//
// Corre desde CI (.github/workflows/build_windows.yml) después de que Inno
// Setup genera el .exe. Requiere BLOB_READ_WRITE_TOKEN como env var — si no
// está configurada, el workflow salta este paso entero (ver el `if:` del
// step), así que este script asume que la variable existe.
//
// Deliberadamente NO usa @vercel/blob como import estático: el paquete se
// instala en el propio step de CI (no vive en node_modules del repo), así
// que se importa dinámicamente para no romper cualquier otro script que
// analice este archivo sin haber corrido `npm install` primero.

const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, 'Output');
const BLOB_PATHNAME = 'installers/MVProjectManagement_Setup_latest.exe';

async function main() {
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) {
    console.log('BLOB_READ_WRITE_TOKEN no está configurada — no se publica.');
    return;
  }

  const archivos = fs.readdirSync(OUTPUT_DIR).filter((f) => f.endsWith('.exe'));
  if (archivos.length !== 1) {
    throw new Error(
      `Se esperaba exactamente un .exe en ${OUTPUT_DIR}, se encontraron ${archivos.length}: ${archivos.join(', ')}`
    );
  }
  const rutaExe = path.join(OUTPUT_DIR, archivos[0]);
  const buffer = fs.readFileSync(rutaExe);

  const { put } = await import('@vercel/blob');
  const resultado = await put(BLOB_PATHNAME, buffer, {
    access: 'public',
    addRandomSuffix: false,
    allowOverwrite: true,
    contentType: 'application/octet-stream',
    token,
  });

  console.log(`Publicado: ${archivos[0]} (${(buffer.length / 1e6).toFixed(1)} MB) -> ${resultado.url}`);
}

main().catch((err) => {
  console.error('Falló la publicación en Vercel Blob:', err);
  process.exit(1);
});
