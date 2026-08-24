// © 2026 Martín Viera. Todos los derechos reservados.
//
// Tablero del dueño — clientes, descargas y dinero, en un solo GET.
//
//     curl -H "Authorization: Bearer <MVPM_OWNER_TOKEN>" \
//          https://<dominio>/api/metricas
//
// Está detrás de un token y no de "una URL difícil de adivinar" porque expone
// facturación y los emails de los clientes. Sin `MVPM_OWNER_TOKEN` configurada
// responde 503 y no sirve nada: el modo por defecto de un endpoint que muestra
// plata tiene que ser cerrado, no abierto.
//
// Lo que devuelve sale medido, nunca estimado: el neto es el que informa
// MercadoPago por pago, y las licencias emitidas son las que están realmente
// registradas en el almacén. Lo que no se puede medir se informa como
// faltante — ver api/_metricas.js.

const crypto = require('crypto');
const { pagosAprobados, resumir } = require('./_metricas');
const { limitar } = require('./_ratelimit');

const PREFIJO_CANJES = 'licencias/canjeadas/';
const PREFIJO_DESCARGAS = 'descargas/';
const PREFIJO_DEMOS = 'demos/';
const PREFIJO_INTENCIONES = 'intenciones/';

function autorizado(req) {
  const esperado = process.env.MVPM_OWNER_TOKEN || '';
  if (!esperado) return false;
  const cabecera = req.headers.authorization || '';
  const enviado = cabecera.startsWith('Bearer ') ? cabecera.slice(7) : '';
  if (!enviado) return false;
  // Longitudes distintas hacen que timingSafeEqual tire; se compara el hash
  // para que el tiempo no dependa de cuántos caracteres acertó quien prueba.
  const h = (s) => crypto.createHash('sha256').update(s).digest();
  return crypto.timingSafeEqual(h(enviado), h(esperado));
}

/** Todo lo que hay bajo un prefijo del Blob, paginando. */
async function listarTodo(prefix, token) {
  const { list } = require('@vercel/blob');
  const items = [];
  let cursor;
  do {
    const pagina = await list({ prefix, token, cursor, limit: 1000 });
    items.push(...(pagina.blobs || []));
    cursor = pagina.hasMore ? pagina.cursor : undefined;
  } while (cursor);
  return items;
}

/** Los canjes registrados, con el payment_id sacado del nombre del archivo. */
async function leerCanjes(token) {
  const blobs = await listarTodo(PREFIJO_CANJES, token);
  const canjes = await Promise.all(blobs.map(async (b) => {
    const id = b.pathname.slice(PREFIJO_CANJES.length).replace(/\.json$/, '');
    try {
      const r = await fetch(b.downloadUrl || b.url);
      const datos = r.ok ? await r.json() : {};
      return { payment_id: id, ...datos };
    } catch {
      // Un registro ilegible sigue siendo un canje que ocurrió: contarlo como
      // inexistente marcaría al cliente como "pagó y no tiene licencia".
      return { payment_id: id };
    }
  }));
  return canjes;
}

module.exports = async (req, res) => {
  if (req.method !== 'GET') { res.status(405).json({ error: 'method' }); return; }
  if (limitar(req, res, 'metricas', { max: 20, ventanaMs: 60_000 })) return;

  if (!process.env.MVPM_OWNER_TOKEN) {
    res.status(503).json({
      error: 'MVPM_OWNER_TOKEN no configurada.',
      como: 'Vercel -> Settings -> Environment Variables -> MVPM_OWNER_TOKEN '
        + '(inventá una cadena larga al azar). Sin eso este endpoint no sirve '
        + 'datos: muestra facturación y emails de clientes.',
    });
    return;
  }
  if (!autorizado(req)) {
    res.status(401).json({ error: 'Falta o no coincide el Authorization: Bearer.' });
    return;
  }

  const mp = process.env.MP_ACCESS_TOKEN;
  const blobToken = process.env.BLOB_READ_WRITE_TOKEN;
  const faltan = [];
  if (!mp) faltan.push('MP_ACCESS_TOKEN (sin esto no hay cifras de dinero)');
  if (!blobToken) faltan.push('BLOB_READ_WRITE_TOKEN (sin esto no hay licencias ni descargas)');

  try {
    const [pagos, canjes, descargas, demos, intenciones] = await Promise.all([
      mp ? pagosAprobados(mp) : Promise.resolve([]),
      blobToken ? leerCanjes(blobToken) : Promise.resolve([]),
      blobToken
        ? listarTodo(PREFIJO_DESCARGAS, blobToken).then((b) => b.length)
        : Promise.resolve(0),
      // Los pedidos de demo. Van acá porque si el aviso por mail falló —el
      // proveedor caído, sin cuota, mal configurado— este es el ÚNICO lugar
      // donde ese pedido aparece. Un pedido que nadie ve es un cliente que no
      // vuelve a escribir.
      blobToken
        ? listarTodo(PREFIJO_DEMOS, blobToken).then((b) => b.length)
        : Promise.resolve(0),
      blobToken
        ? listarTodo(PREFIJO_INTENCIONES, blobToken).then((b) => b.length)
        : Promise.resolve(0),
    ]);

    const resumen = resumir({ pagos, canjes, descargas });
    resumen.demos = { pedidas: demos };
    // Clicks en "Comprar" contra pagos aprobados. La diferencia es la gente
    // que quiso comprar y no pudo — el número que ningún panel de MercadoPago
    // muestra, porque para MercadoPago esa venta nunca existió.
    resumen.intenciones = {
      clicks_comprar: intenciones,
      sin_concretar: Math.max(0, intenciones - resumen.pagos.aprobados),
    };
    // Se dice qué NO se pudo medir, en vez de devolver ceros que se leen como
    // "todavía no vendiste nada".
    resumen.sin_medir = faltan;
    resumen.generado_en = new Date().toISOString();
    res.status(200).json(resumen);
  } catch (e) {
    res.status(502).json({
      error: 'No se pudieron reunir las métricas.',
      detalle: String(e.message || e).slice(0, 200),
      sin_medir: faltan,
    });
  }
};
