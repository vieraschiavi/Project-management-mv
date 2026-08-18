// © 2026 Martín Viera. Todos los derechos reservados.
// Licencias firmadas — mismo esquema que mvpm/licensing.py en Python
// (formato "MVPM2.<payload_b64url>.<firma_b64url>").
//
// Firma ASIMÉTRICA Ed25519, no un secreto compartido: acá vive la clave
// PRIVADA (MVPM_LICENSE_PRIVATE_KEY, variable de entorno de Vercel) y en el
// programa del cliente viaja sólo la PÚBLICA, que verifica pero no emite.
//
// El esquema anterior era HMAC con MVPM_LICENSE_SECRET "compartido", y estaba
// roto en las dos direcciones: el cliente, al no tener esa variable, se
// autogeneraba un secreto local, así que (a) podía emitirse una licencia
// Enterprise solo y (b) el token que emitía ESTA función no le verificaba —
// pagaba y seguía viendo "la prueba venció". Con Ed25519 las dos se caen: sin
// la clave privada no se produce una firma que la pública acepte.

const crypto = require('crypto');

const PLANES = {
  demo: { nombre: 'Demo de evaluación', precio_usd: 0, cupo_mensual_ia: 20 },
  professional: { nombre: 'Professional', precio_usd: 9, cupo_mensual_ia: 1000 },
  professional_anual: { nombre: 'Professional (12 meses)', precio_usd: 90, cupo_mensual_ia: 1000 },
  enterprise: { nombre: 'Enterprise', precio_usd: null, cupo_mensual_ia: null },
};

// Node no toma los 32 bytes crudos de una clave Ed25519 directamente: hay que
// envolverlos en DER. Estos son los encabezados fijos de la norma (PKCS#8 para
// la privada, SPKI para la pública); lo único que cambia es la clave que va
// pegada atrás. Se usa el mismo formato crudo base64url que Python, para que
// el par que genera packaging/generar_claves_licencia.py sirva de los dos lados.
const DER_PRIVADA = Buffer.from('302e020100300506032b657004220420', 'hex');
const DER_PUBLICA = Buffer.from('302a300506032b6570032100', 'hex');

function b64url(buf) {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function b64urlDecode(str) {
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) str += '=';
  return Buffer.from(str, 'base64');
}

function clavePrivada() {
  const cruda = process.env.MVPM_LICENSE_PRIVATE_KEY;
  if (!cruda) {
    // En Vercel la clave SIEMPRE debe venir de una env var (no hay disco
    // persistente entre invocaciones de una función serverless). Si falta,
    // fallamos explícito en vez de emitir licencias que nadie va a poder
    // verificar.
    throw new Error('MVPM_LICENSE_PRIVATE_KEY no configurada');
  }
  const semilla = b64urlDecode(cruda);
  if (semilla.length !== 32) {
    throw new Error('MVPM_LICENSE_PRIVATE_KEY inválida: se esperaban 32 bytes');
  }
  return crypto.createPrivateKey({
    key: Buffer.concat([DER_PRIVADA, semilla]),
    format: 'der',
    type: 'pkcs8',
  });
}

//: La clave pública que viaja DENTRO del programa que usa el cliente. Tiene
//: que decir exactamente lo mismo que CLAVE_PUBLICA_EMBEBIDA en
//: mvpm/licensing.py — es la única con la que una instalación puede verificar
//: una licencia. Lo fija tests/test_licencias.js.
const CLAVE_PUBLICA_EMBEBIDA = 'Ba7bsdl1pysbGEuG6wa3fne1PfdsTbkIpo8DD7cIgMg';

function clavePublicaDelPrograma() {
  // Misma precedencia que `_clave_publica()` en mvpm/licensing.py: la variable
  // de entorno le gana a la embebida. En producción no está seteada, así que
  // manda la embebida —que es la que trae la copia del cliente— y por eso el
  // chequeo sirve. En los tests sí se setea, con el par efímero de la corrida:
  // las claves reales no están en el repo y no deben estarlo.
  const cruda = (process.env.MVPM_LICENSE_PUBLIC_KEY || '').trim()
    || CLAVE_PUBLICA_EMBEBIDA;
  return crypto.createPublicKey({
    key: Buffer.concat([DER_PUBLICA, b64urlDecode(cruda)]),
    format: 'der',
    type: 'spki',
  });
}

function clavePublica() {
  // Sólo hace falta para verificar del lado del servidor (tests, diagnóstico).
  // Se deriva de la privada si no viene explícita, así no hay dos fuentes de
  // verdad que se puedan desincronizar.
  const cruda = process.env.MVPM_LICENSE_PUBLIC_KEY;
  if (cruda) {
    return crypto.createPublicKey({
      key: Buffer.concat([DER_PUBLICA, b64urlDecode(cruda)]),
      format: 'der',
      type: 'spki',
    });
  }
  return crypto.createPublicKey(clavePrivada());
}

function issueLicense(plan, email, paymentId = null) {
  if (!PLANES[plan]) throw new Error(`Plan desconocido: ${plan}`);
  const payload = {
    plan, email, payment_id: paymentId,
    iat: Math.floor(Date.now() / 1000),
    cupo_mensual_ia: PLANES[plan].cupo_mensual_ia,
  };
  const payloadB64 = b64url(Buffer.from(JSON.stringify(payload)));
  // Ed25519 firma el mensaje entero (no un digest previo): algoritmo null.
  const sig = crypto.sign(null, Buffer.from(payloadB64, 'ascii'), clavePrivada());
  const token = `MVPM2.${payloadB64}.${b64url(sig)}`;

  // El token se verifica contra la clave que viaja en el PROGRAMA, no contra
  // la que se deriva de la privada.
  //
  // Sin esto, una MVPM_LICENSE_PRIVATE_KEY que no sea la del par de producción
  // produce un token perfectamente firmado y coherente consigo mismo: el
  // servidor responde 200 con su `license_token`, el cliente lo pega en la app
  // y la app lo rechaza. Nadie se entera hasta que alguien paga, y para
  // entonces ya cobraste por algo que no abre. Mejor que falle la emisión
  // —ruidoso, visible, del lado del servidor— a vender una licencia muerta.
  if (!crypto.verify(null, Buffer.from(payloadB64, 'ascii'),
                     clavePublicaDelPrograma(), b64urlDecode(b64url(sig)))) {
    throw new Error(
      'MVPM_LICENSE_PRIVATE_KEY no corresponde a la clave pública embebida en ' +
      'el programa: la licencia emitida no la podría verificar ninguna ' +
      'instalación. Revisá la variable de entorno en Vercel.');
  }
  return token;
}

// Tokens emitidos de verdad que dejaron de valer, por su firma. Tiene que
// decir exactamente lo mismo que FIRMAS_REVOCADAS en mvpm/licensing.py: si las
// dos listas se desincronizan, el servidor sigue aceptando un token que el
// programa ya rechaza (o al revés). Lo fija tests/test_licencias_js.test.js.
const FIRMAS_REVOCADAS = new Set([
  // packaging/OWNER_EDITION — enterprise, quedó versionado en un repo público.
  '7toxxzkepMP3F1giHxrDlwsiHuSGItLuG56s3aRGOhhjoXElTc9zWP8WexWa8leXFbeYf4zG3m8C57GWlR_YDw',
]);

function verifyLicense(token) {
  try {
    const [prefix, payloadB64, sigB64] = token.split('.');
    if (prefix !== 'MVPM2') return null;
    if (FIRMAS_REVOCADAS.has(sigB64)) return null;
    const ok = crypto.verify(
      null, Buffer.from(payloadB64, 'ascii'), clavePublica(), b64urlDecode(sigB64));
    if (!ok) return null;
    return JSON.parse(b64urlDecode(payloadB64).toString('utf-8'));
  } catch (e) {
    return null;
  }
}

module.exports = { PLANES, issueLicense, verifyLicense, FIRMAS_REVOCADAS,
                   CLAVE_PUBLICA_EMBEBIDA, clavePublicaDelPrograma };
