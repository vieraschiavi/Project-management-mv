// Registro de pagos ya canjeados por una licencia — idempotencia de
// api/verify-payment.js.
//
// El problema que resuelve: ese endpoint es un GET público y no registraba
// nada, así que un mismo `payment_id` se podía canjear infinitas veces y, como
// el email de la licencia salía del query string cuando MercadoPago no manda
// `payer.email`, UN pago de US$9 alcanzaba para emitir licencias a nombre de
// cuanta gente quisiera quien tuviera ese id.
//
// Qué hace ahora: el primer canje deja registrado `payment_id -> {plan, email}`.
// Los canjes siguientes NO fallan —el cliente que recarga la página de retorno
// tiene que recibir su licencia igual— pero se re-emiten para el plan y el
// email del PRIMER canje, ignorando lo que venga por la URL. Un pago sigue
// valiendo una licencia, la de quien pagó.
//
// El almacén es Vercel Blob, que ya se usa para publicar el instalador: las
// funciones serverless no tienen disco propio entre invocaciones.

// El require es perezoso a propósito: en Vercel `@vercel/blob` está siempre
// (va en package.json), pero la suite de tests corre sin `npm install`, y
// api/verify-payment.js tiene que poder cargarse igual para poder testear todo
// lo que no toca el almacén (validación de plan, de monto, de estado del pago).
function blob() {
  return require('@vercel/blob');
}

const PREFIJO = 'licencias/canjeadas/';

function rutaDe(paymentId) {
  // El id de MercadoPago es numérico; se sanea igual por las dudas, para que
  // nadie pueda armar rutas raras dentro del bucket.
  return `${PREFIJO}${String(paymentId).replace(/[^A-Za-z0-9_-]/g, '')}.json`;
}

function token() {
  return process.env.BLOB_READ_WRITE_TOKEN || '';
}

/** El canje previo de este pago, o null si es la primera vez.
 *  Devuelve null también si el almacén no está configurado. */
async function canjePrevio(paymentId) {
  if (!token()) return null;
  try {
    const meta = await blob().head(rutaDe(paymentId), { token: token() });
    const res = await fetch(meta.downloadUrl || meta.url);
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    return null; // no existe todavía (head tira si no lo encuentra)
  }
}

/** Deja registrado que este pago ya emitió una licencia. */
async function registrarCanje(paymentId, plan, email) {
  if (!token()) {
    // Se avisa fuerte pero no se bloquea la emisión: el cliente ya pagó y
    // dejarlo sin licencia por un problema de configuración nuestra es peor.
    console.error(
      'BLOB_READ_WRITE_TOKEN no configurada: no se puede registrar el canje del ' +
      `pago ${paymentId}. Ese pago se puede volver a canjear para otro email.`);
    return;
  }
  const registro = { plan, email, canjeado_en: new Date().toISOString() };
  await blob().put(rutaDe(paymentId), JSON.stringify(registro), {
    access: 'public',
    contentType: 'application/json',
    addRandomSuffix: false, // la ruta tiene que ser estable para poder consultarla
    token: token(),
  });
}

module.exports = { canjePrevio, registrarCanje };
