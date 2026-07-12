// Licencias firmadas — mismo esquema HMAC que mvpm/licensing.py en Python
// (formato "MVPM1.<payload_b64url>.<firma_b64url>", mismo secreto compartido
// vía MVPM_LICENSE_SECRET) para que ambos lados puedan emitir y verificar el
// mismo token sin depender de una librería JWT externa.

const crypto = require('crypto');

const PLANES = {
  demo: { nombre: 'Demo de evaluación', precio_usd: 0, cupo_mensual_ia: 20 },
  professional: { nombre: 'Professional', precio_usd: 9, cupo_mensual_ia: 1000 },
  enterprise: { nombre: 'Enterprise', precio_usd: null, cupo_mensual_ia: null },
};

function secret() {
  const s = process.env.MVPM_LICENSE_SECRET;
  if (!s) {
    // En Vercel el secreto SIEMPRE debe venir de una env var (no hay disco
    // persistente entre invocaciones de una función serverless). Si falta,
    // fallamos explícito en vez de emitir licencias con un secreto que
    // cambia en cada cold start.
    throw new Error('MVPM_LICENSE_SECRET no configurada');
  }
  return s;
}

function b64url(buf) {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function b64urlDecode(str) {
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) str += '=';
  return Buffer.from(str, 'base64');
}

function issueLicense(plan, email, paymentId = null) {
  if (!PLANES[plan]) throw new Error(`Plan desconocido: ${plan}`);
  const payload = {
    plan, email, payment_id: paymentId,
    iat: Math.floor(Date.now() / 1000),
    cupo_mensual_ia: PLANES[plan].cupo_mensual_ia,
  };
  const payloadB64 = b64url(Buffer.from(JSON.stringify(payload)));
  const sig = crypto.createHmac('sha256', secret()).update(payloadB64).digest();
  return `MVPM1.${payloadB64}.${b64url(sig)}`;
}

function verifyLicense(token) {
  try {
    const [prefix, payloadB64, sigB64] = token.split('.');
    if (prefix !== 'MVPM1') return null;
    const expected = crypto.createHmac('sha256', secret()).update(payloadB64).digest();
    const actual = b64urlDecode(sigB64);
    if (expected.length !== actual.length || !crypto.timingSafeEqual(expected, actual)) return null;
    return JSON.parse(b64urlDecode(payloadB64).toString('utf-8'));
  } catch (e) {
    return null;
  }
}

module.exports = { PLANES, issueLicense, verifyLicense };
