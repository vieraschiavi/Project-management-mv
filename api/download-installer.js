// © 2026 Martín Viera. Todos los derechos reservados.
// Descarga del instalador de Windows — función serverless (Vercel, CommonJS).
//
// ## Ya no es pública, y el motivo no es el ancho de banda
//
// Este endpoint entregaba el `.exe` a cualquiera que supiera la URL. Junto con
// el ZIP que colgaba de la home, eso significaba que el producto entero se
// bajaba sin dejar rastro de quién ni por qué. Ahora la demo se pide y se
// muestra en vivo (`api/solicitar-demo.js`), y el instalador se entrega
// solamente a quien ya tiene licencia.
//
// ## La licencia ES la credencial, y por eso no hay almacén nuevo
//
// Quien paga recibe un token `MVPM2` firmado con Ed25519. Ese mismo token
// abre esta descarga: se verifica con la clave PÚBLICA, que ya vive acá.
// Emitirlo requiere la clave privada, que sólo tiene Vercel, así que nadie se
// fabrica un permiso de descarga — es exactamente la misma garantía que
// sostiene el candado del programa, sin una segunda lista de tokens que
// mantener sincronizada.
//
// Se acepta por `Authorization: Bearer`, por `?token=` o por el cuerpo, porque
// el caso normal es un enlace que el cliente abre en el navegador después de
// pagar, y ahí sólo hay query string.

// El require de `@vercel/blob` es perezoso, igual que en `api/_canjes.js`: en
// Vercel el paquete está siempre, pero la suite corre sin `npm install`, y sin
// esto el módulo entero no se puede cargar — o sea que la parte que MÁS
// importa testear (que no se entregue el instalador sin licencia) quedaría sin
// cubrir por una dependencia que ni siquiera participa de esa decisión.
const { verifyLicense } = require('./_license');
const { limitar } = require('./_ratelimit');

const BLOB_PATHNAME = 'installers/MVProjectManagement_Setup_latest.exe';
const CONTACTO = 'vieraschiavi@gmail.com';

function tokenDe(req) {
  const cabecera = req.headers.authorization || '';
  if (cabecera.startsWith('Bearer ')) return cabecera.slice(7).trim();
  const q = (req.query && (req.query.token || req.query.licencia)) || '';
  if (q) return String(q).trim();
  const b = req.body;
  if (b && typeof b === 'object' && b.token) return String(b.token).trim();
  return '';
}

/** Un objeto minúsculo por descarga; `api/metricas.js` los cuenta listando.
 *
 * Se guarda la fecha y el plan, nada más — ni IP, ni user agent, ni el mail.
 * Alcanza para el número que el tablero necesita y evita acumular datos
 * personales que nadie va a mirar. */
async function anotarDescarga(token, plan) {
  const { put } = require('@vercel/blob');
  const ahora = new Date();
  const dia = ahora.toISOString().slice(0, 10);
  await put(
    `descargas/${dia}/${ahora.getTime()}-${Math.random().toString(36).slice(2, 8)}.json`,
    JSON.stringify({ en: ahora.toISOString(), plan: plan || null }),
    { access: 'public', contentType: 'application/json', token },
  );
}

module.exports = async (req, res) => {
  // 30/min por IP: reintentar una descarga cortada es legítimo; lo que corta
  // es el scraping en bucle.
  if (limitar(req, res, 'download-installer', { max: 30, ventanaMs: 60_000 })) return;

  const licencia = tokenDe(req);
  if (!licencia) {
    res.status(401).json({
      error: 'falta_licencia',
      mensaje: 'El instalador se entrega a clientes con licencia. Para verlo '
        + 'funcionando, pedí una demo en la web y lo mostramos en vivo.',
      contacto: CONTACTO,
    });
    return;
  }

  const payload = verifyLicense(licencia);
  if (!payload) {
    // Mismo mensaje para "token inventado" y "token vencido": distinguirlos
    // le diría a quien prueba tokens cuándo va por buen camino.
    res.status(403).json({
      error: 'licencia_invalida',
      mensaje: 'Esa licencia no es válida. Si acabás de pagar y te da esto, '
        + `escribinos a ${CONTACTO}.`,
      contacto: CONTACTO,
    });
    return;
  }

  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) {
    res.status(503).json({
      error: 'no_publicado',
      mensaje: `El instalador todavía no está publicado. Escribinos a ${CONTACTO} y te lo mandamos.`,
    });
    return;
  }

  try {
    const { head } = require('@vercel/blob');
    const meta = await head(BLOB_PATHNAME, { token });
    // Se anota antes de redirigir pero sin poder romper la descarga: si el
    // registro falla, el cliente igual se lleva su instalador. Un contador no
    // puede ser motivo para que una descarga no ocurra.
    await anotarDescarga(token, payload.plan).catch(() => {});
    res.writeHead(302, { Location: meta.downloadUrl || meta.url });
    res.end();
  } catch (err) {
    res.status(404).json({
      error: 'no_publicado',
      mensaje: `El instalador todavía no está publicado. Escribinos a ${CONTACTO} y te lo mandamos.`,
    });
  }
};

module.exports.tokenDe = tokenDe;
