// © 2026 Martín Viera. Todos los derechos reservados.
//
// Avisos al dueño: se registran SIEMPRE, se mandan por mail si se puede.
//
// El orden importa y es el mismo que ya usaba `api/solicitar-demo.js`:
// primero el registro en Vercel Blob, después el mail. El mail depende de un
// servicio externo que puede estar caído, sin cuota o mal configurado; el
// registro no. Al revés quedaría un aviso sin registro; así queda un registro
// sin aviso, que se recupera solo mirando `/api/metricas`.
//
// Nada de lo que hay acá puede tumbar la operación que lo llama. Un aviso que
// falla es una molestia; un checkout que no se abre porque el mail falló es
// una venta perdida.

const crypto = require('crypto');

const DESTINO = 'vieraschiavi@gmail.com';

/** Identificador estable y ANÓNIMO de quien pide, para deduplicar.
 *
 * Se hashea la IP en vez de guardarla. Lo que hace falta es distinguir a dos
 * personas entre sí, no saber quién es ninguna: un hash cumple eso y no deja
 * un dato personal acumulado de gente que todavía ni siquiera es cliente. */
function huella(req) {
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim()
    || (req.socket && req.socket.remoteAddress) || 'sin-ip';
  return crypto.createHash('sha256').update(ip).digest('hex').slice(0, 16);
}

function escapar(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/**
 * Deja el hecho registrado en el almacén. Devuelve true/false, nunca lanza.
 *
 * `prefijo` termina en `/` y agrupa por tipo (`demos/`, `intenciones/`), y
 * dentro por día, para que listar un mes no traiga todo el histórico.
 */
async function registrar(prefijo, datos) {
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) return false;
  try {
    const { put } = require('@vercel/blob');
    const ahora = new Date().toISOString();
    const clave = `${prefijo}${ahora.slice(0, 10)}/${Date.now()}-`
      + `${Math.random().toString(36).slice(2, 8)}.json`;
    await put(clave, JSON.stringify({ ...datos, en: ahora }), {
      access: 'public', contentType: 'application/json', token,
    });
    return true;
  } catch (e) {
    console.error(`No se pudo registrar en ${prefijo}:`, String(e.message || e));
    return false;
  }
}

/**
 * Registra el hecho UNA sola vez por clave, y dice si era nuevo.
 *
 * El problema que resuelve: alguien indeciso que aprieta "Comprar" cinco veces
 * generaba cinco registros y cinco mails. A la tercera notificación idéntica
 * uno deja de mirarlas, y ahí el aviso deja de servir para lo único que sirve.
 *
 * La ruta es determinista —día + huella + clave— y `addRandomSuffix: false`,
 * así el segundo `put` pisa al primero en vez de sumar. El `head` previo es lo
 * que distingue "primera vez" de "otra vez": si ya existe, se registra igual
 * (para que el dato quede fresco) pero se devuelve `nuevo: false` y quien
 * llama decide no mandar el mail.
 *
 * Se deduplica POR DÍA. Alguien que vuelve mañana es una intención nueva de
 * verdad, y ahí sí querés enterarte.
 */
async function registrarUnaVez(prefijo, clave, datos) {
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) return { registrado: false, nuevo: true };
  const dia = new Date().toISOString().slice(0, 10);
  const ruta = `${prefijo}${dia}/${String(clave).replace(/[^A-Za-z0-9_-]/g, '_')}.json`;
  let nuevo = true;
  try {
    const { head, put } = require('@vercel/blob');
    try {
      await head(ruta, { token });
      nuevo = false;      // ya existía: mismo día, misma persona, mismo plan
    } catch (_) { /* no existe todavía: es la primera vez */ }
    await put(ruta, JSON.stringify({ ...datos, en: new Date().toISOString() }), {
      access: 'public', contentType: 'application/json',
      addRandomSuffix: false, allowOverwrite: true, token,
    });
    return { registrado: true, nuevo };
  } catch (e) {
    console.error(`No se pudo registrar en ${prefijo}:`, String(e.message || e));
    // Si el almacén falla no se puede saber si era repetido. Se devuelve
    // `nuevo: true` a propósito: mejor un mail de más que perderse el aviso
    // de que alguien quiso comprar.
    return { registrado: false, nuevo: true };
  }
}

/**
 * Manda el aviso por mail. Devuelve {enviado, motivo}, nunca lanza.
 *
 * `responderA` es opcional y va en `reply_to`, nunca en `from`: poner el mail
 * de un tercero como remitente hace que el correo se rechace por SPF y no
 * llegue nunca.
 */
async function porMail({ asunto, filas, extra = '', responderA = null }) {
  const clave = process.env.RESEND_API_KEY;
  const desde = process.env.DEMO_FROM_EMAIL;
  if (!clave || !desde) return { enviado: false, motivo: 'sin_proveedor' };

  const cuerpo = filas
    .map(([k, v]) => `<tr><td><b>${escapar(k)}</b></td><td>${escapar(v)}</td></tr>`)
    .join('');
  try {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${clave}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: desde,
        to: [DESTINO],
        ...(responderA ? { reply_to: responderA } : {}),
        subject: asunto,
        html: `<h2>${escapar(asunto)}</h2><table>${cuerpo}</table>${extra}`,
      }),
    });
    return r.ok ? { enviado: true } : { enviado: false, motivo: `resend_${r.status}` };
  } catch (e) {
    return { enviado: false, motivo: `fetch_${String(e.message || e).slice(0, 40)}` };
  }
}

module.exports = { registrar, registrarUnaVez, porMail, escapar, huella, DESTINO };
