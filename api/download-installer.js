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
    res.writeHead(302, { Location: meta.downloadUrl || meta.url });
    res.end();
  } catch (err) {
    res.status(404).send(
      `El instalador de Windows todavía no está publicado. Escribinos a ${CONTACTO} y te lo mandamos.`
    );
  }
};
