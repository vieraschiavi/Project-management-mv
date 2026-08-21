// © 2026 Martín Viera. Todos los derechos reservados.
//
// Pedido de demo — la demo se muestra en vivo, no se descarga.
//
// El criterio, y por qué el código está armado así:
//
// * **No se regala el artefacto de ingeniería.** Antes la home tenía un botón
//   que bajaba un ZIP con 39 módulos de `mvpm/` en `.py` legible. El
//   instalador se molesta en compilar el motor a `.pyd`
//   (`packaging/strip_py_sources.py`) precisamente para que eso no pase; el
//   ZIP anulaba esa protección y encima no dejaba rastro de quién se lo llevó.
// * **Queda el rastro.** Nombre, empresa, país y mail de cada persona que
//   pide ver el producto. Un competidor mirando también deja su huella, o no
//   entra.
// * **La demo es una reunión.** Se muestra y se vende al mismo tiempo, en vez
//   de que alguien mire solo diez minutos y se vaya sin decir nada.
//
// Este endpoint NO entrega nada descargable y no puede: no conoce ninguna URL
// de instalador. Sólo registra el pedido y avisa.
//
// ## Por qué se guarda ANTES de mandar el mail
//
// El mail depende de un servicio externo que puede estar caído, sin cuota o
// mal configurado. El pedido, no. Si se mandara primero y el guardado fallara,
// habría un aviso sin registro; al revés hay un registro sin aviso, que se
// recupera solo mirando `/api/metricas`. Un pedido perdido es un cliente
// perdido, y no hay forma de enterarse: la persona no vuelve a escribir.

const { limitar } = require('./_ratelimit');

const DESTINO = 'vieraschiavi@gmail.com';
const PREFIJO = 'demos/';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

//: Tope por campo. No es una validación de negocio: es que nada de lo que
//: escriba un desconocido termine siendo un objeto de varios MB en el almacén
//: ni un asunto de mail de mil caracteres.
const LARGO = { nombre: 120, email: 254, empresa: 120, pais: 60, mensaje: 2000 };

function texto(valor, max) {
  return String(valor === undefined || valor === null ? '' : valor)
    .replace(/[\r\n\t]+/g, ' ')   // nada de saltos: van a un asunto de mail
    .trim()
    .slice(0, max);
}

function escapar(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/** Valida el pedido. Devuelve {datos} o {error} con el campo que falla. */
function validar(body) {
  const datos = {
    nombre: texto(body.nombre, LARGO.nombre),
    email: texto(body.email, LARGO.email).toLowerCase(),
    empresa: texto(body.empresa, LARGO.empresa),
    pais: texto(body.pais, LARGO.pais),
    // El mensaje es opcional y admite saltos de línea: no va al asunto.
    mensaje: String(body.mensaje || '').trim().slice(0, LARGO.mensaje),
  };
  // Los cuatro primeros son obligatorios: son los que convierten "alguien
  // miró" en "sé con quién estoy hablando".
  for (const campo of ['nombre', 'email', 'empresa', 'pais']) {
    if (!datos[campo]) return { error: `falta_${campo}` };
  }
  // Nombre COMPLETO: un solo token es "juan" y no sirve para nada.
  if (!/\s/.test(datos.nombre)) return { error: 'nombre_incompleto' };
  if (!EMAIL_RE.test(datos.email)) return { error: 'email_invalido' };
  return { datos };
}

async function registrar(datos, origen) {
  const token = process.env.BLOB_READ_WRITE_TOKEN;
  if (!token) return false;
  const { put } = require('@vercel/blob');
  const ahora = new Date().toISOString();
  const clave = `${PREFIJO}${ahora.slice(0, 10)}/${Date.now()}-`
    + `${datos.email.replace(/[^a-z0-9]/g, '_').slice(0, 40)}.json`;
  await put(clave, JSON.stringify({ ...datos, pedido_en: ahora, origen }), {
    access: 'public', contentType: 'application/json', token,
  });
  return true;
}

async function avisar(datos) {
  const clave = process.env.RESEND_API_KEY;
  const desde = process.env.DEMO_FROM_EMAIL;
  if (!clave || !desde) return { enviado: false, motivo: 'sin_proveedor' };

  const cuerpo = [
    ['Nombre', datos.nombre], ['Empresa', datos.empresa],
    ['País', datos.pais], ['Email', datos.email],
  ].map(([k, v]) => `<tr><td><b>${escapar(k)}</b></td><td>${escapar(v)}</td></tr>`)
    .join('');
  const mensaje = datos.mensaje
    ? `<p style="white-space:pre-wrap">${escapar(datos.mensaje)}</p>` : '';

  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${clave}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from: desde,
      to: [DESTINO],
      // `reply_to` y no `from`: poner el mail del solicitante como remitente
      // haría que el correo se rechace por SPF y no llegue nunca.
      reply_to: datos.email,
      subject: `Demo pedida — ${datos.nombre} (${datos.empresa}, ${datos.pais})`,
      html: `<h2>Pedido de demo</h2><table>${cuerpo}</table>${mensaje}`,
    }),
  });
  return r.ok ? { enviado: true } : { enviado: false, motivo: `resend_${r.status}` };
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') { res.status(405).json({ error: 'method' }); return; }
  // 5/min por IP. Un pedido de demo no se hace en loop, y acá no hay ningún
  // paso de pago que frene el abuso por costo como en el checkout.
  if (limitar(req, res, 'solicitar-demo', { max: 5, ventanaMs: 60_000 })) return;

  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch { body = {}; }
  }
  const { datos, error } = validar(body || {});
  if (error) { res.status(400).json({ error }); return; }

  let registrado = false;
  try {
    registrado = await registrar(datos, texto(req.headers.referer, 200));
  } catch (e) {
    console.error('No se pudo registrar el pedido de demo:', String(e.message || e));
  }

  let aviso = { enviado: false, motivo: 'no_intentado' };
  try {
    aviso = await avisar(datos);
  } catch (e) {
    aviso = { enviado: false, motivo: String(e.message || e).slice(0, 80) };
  }

  if (!registrado && !aviso.enviado) {
    // Ninguno de los dos caminos funcionó: el pedido se perdería en silencio.
    // Mejor que la persona vea un error y escriba al mail, a agradecerle por
    // algo que nadie va a leer.
    console.error('PEDIDO DE DEMO PERDIDO:', datos.email, aviso.motivo);
    res.status(503).json({
      error: 'no_registrado',
      escribinos: DESTINO,
    });
    return;
  }

  // La respuesta es la misma haya salido el mail o no: si el aviso falló, el
  // pedido igual quedó registrado y aparece en /api/metricas. Contarle al
  // visitante en qué estado está nuestra infraestructura no le sirve de nada.
  res.status(200).json({ ok: true, contacto: DESTINO });
};

module.exports.validar = validar;
module.exports.escapar = escapar;
module.exports.DESTINO = DESTINO;
module.exports.PREFIJO = PREFIJO;
