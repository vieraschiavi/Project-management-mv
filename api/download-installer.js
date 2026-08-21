// © 2026 Martín Viera. Todos los derechos reservados.
// Descarga del instalador de Windows — función serverless (Vercel, CommonJS).
//
// El repo es privado a propósito, así que un link directo a un asset de
// GitHub Release no sirve: un visitante anónimo de la landing no tiene
// permiso para bajarlo. En cambio, build_windows.yml sube el .exe compilado
// a Vercel Blob (público) con un nombre de archivo FIJO en cada build
// exitoso — acá sólo se resuelve esa URL en el momento del click y se
// redirige. Así el botón de la landing nunca cambia entre releases.
//
// Mismo patrón CommonJS que api/checkout.js y api/verify-payment.js.

const { head } = require('@vercel/blob');
const { limitar } = require('./_ratelimit');

const BLOB_PATHNAME = 'installers/MVProjectManagement_Setup_latest.exe';
const CONTACTO = 'vieraschiavi@gmail.com';

/** Un objeto minúsculo por descarga; `api/metricas.js` los cuenta listando.
 *
 * Se guarda la fecha y nada más — ni IP ni user agent. Alcanza para el número
 * que el tablero necesita ("cuántas descargas") y evita acumular datos
 * personales de gente que todavía ni siquiera es cliente. */
async function anotarDescarga(token) {
  const { put } = require('@vercel/blob');
  const ahora = new Date();
  const dia = ahora.toISOString().slice(0, 10);
  await put(
    `descargas/${dia}/${ahora.getTime()}-${Math.random().toString(36).slice(2, 8)}.json`,
    JSON.stringify({ en: ahora.toISOString() }),
    { access: 'public', contentType: 'application/json', token },
  );
}

module.exports = async (req, res) => {
  // Cada llamada resuelve la URL del blob contra la API de Vercel. El límite
  // es holgado (30/min por IP) porque bajar el instalador varias veces es un
  // uso legítimo; sólo corta el scraping en bucle.
  if (limitar(req, res, 'download-installer', { max: 30, ventanaMs: 60_000 })) return;

  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) {
    res.status(503).send(
      `El instalador de Windows todavía no está publicado. Escribinos a ${CONTACTO} y te lo mandamos.`
    );
    return;
  }

  try {
    const meta = await head(BLOB_PATHNAME, { token });
    // Se anota la descarga ANTES de redirigir pero sin poder romperla: si el
    // registro falla, la persona igual se lleva su instalador. Un contador no
    // puede ser motivo para que una descarga no ocurra.
    await anotarDescarga(token).catch(() => {});
    res.writeHead(302, { Location: meta.downloadUrl || meta.url });
    res.end();
  } catch (err) {
    res.status(404).send(
      `El instalador de Windows todavía no está publicado. Escribinos a ${CONTACTO} y te lo mandamos.`
    );
  }
};
