// © 2026 Martín Viera. Todos los derechos reservados.
//
// Responde si ESTA instalación de producción puede emitir licencias que el
// programa del cliente vaya a aceptar.
//
// El problema que resuelve: `_license.js` deriva la clave pública de la
// privada, así que el servidor siempre es coherente CONSIGO MISMO. Si la
// MVPM_LICENSE_PRIVATE_KEY configurada en Vercel no es la del par de
// producción, la emisión sale perfecta —200, token bien firmado— y el token no
// lo verifica ninguna instalación, porque el programa trae embebida la OTRA
// clave pública. Eso no se descubre con un test ni con un deploy verde: se
// descubre cuando alguien ya pagó.
//
// Este endpoint lo dice antes, sin cobrar nada:
//
//     curl https://<dominio>/api/estado-licencias
//
// Devuelve SÓLO booleanos. Nunca la clave privada, nunca un token: si firmara
// algo que le pidan, sería una fábrica de licencias gratis para cualquiera que
// encuentre la URL. La comparación se hace derivando la pública de la privada
// y comparándola con la embebida — no hace falta firmar nada.

const crypto = require('crypto');
const { CLAVE_PUBLICA_EMBEBIDA } = require('./_license');
const { limitar } = require('./_ratelimit');

function b64url(buf) {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function b64urlDecode(str) {
  str = str.replace(/-/g, '+').replace(/_/g, '/');
  while (str.length % 4) str += '=';
  return Buffer.from(str, 'base64');
}

const DER_PRIVADA = Buffer.from('302e020100300506032b657004220420', 'hex');

/** Los 32 bytes crudos de la pública que corresponde a la privada configurada. */
function publicaDeLaPrivada() {
  const cruda = process.env.MVPM_LICENSE_PRIVATE_KEY;
  if (!cruda) return null;
  const semilla = b64urlDecode(cruda.trim());
  if (semilla.length !== 32) return 'largo_invalido';
  const privada = crypto.createPrivateKey({
    key: Buffer.concat([DER_PRIVADA, semilla]), format: 'der', type: 'pkcs8',
  });
  const spki = crypto.createPublicKey(privada).export({ format: 'der', type: 'spki' });
  // Los últimos 32 bytes del SPKI son la clave; el resto es el encabezado DER.
  return b64url(spki.subarray(spki.length - 32));
}

module.exports = (req, res) => {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'method' });
    return;
  }
  // Era el único endpoint sin límite, y no es gratis: cada llamada deriva una
  // clave Ed25519 desde la privada. Un bucle contra esta URL quema CPU e
  // invocaciones sin que nadie tenga que autenticarse. 10/min alcanza de sobra
  // para lo que existe: mirarlo después de configurar una variable.
  if (limitar(req, res, 'estado-licencias', { max: 10, ventanaMs: 60_000 })) return;

  const pagos_configurados = Boolean(process.env.MP_ACCESS_TOKEN);

  let derivada;
  try {
    derivada = publicaDeLaPrivada();
  } catch (e) {
    res.status(200).json({
      ok: false,
      privada_configurada: true,
      coincide_con_el_programa: false,
      pagos_configurados,
      motivo: 'MVPM_LICENSE_PRIVATE_KEY no se puede leer como clave Ed25519.',
    });
    return;
  }

  if (derivada === null) {
    res.status(200).json({
      ok: false,
      privada_configurada: false,
      coincide_con_el_programa: false,
      pagos_configurados,
      motivo: 'Falta MVPM_LICENSE_PRIVATE_KEY: un cliente que pague recibiría '
        + 'un error 500 en vez de su licencia.',
    });
    return;
  }

  if (derivada === 'largo_invalido') {
    res.status(200).json({
      ok: false,
      privada_configurada: true,
      coincide_con_el_programa: false,
      pagos_configurados,
      motivo: 'MVPM_LICENSE_PRIVATE_KEY no mide 32 bytes.',
    });
    return;
  }

  const coincide = derivada === CLAVE_PUBLICA_EMBEBIDA;
  res.status(200).json({
    ok: coincide && pagos_configurados,
    privada_configurada: true,
    coincide_con_el_programa: coincide,
    pagos_configurados,
    motivo: coincide
      ? 'La licencia que emita este servidor la verifica el programa del cliente.'
      : 'La clave privada NO es la del par de producción: se emitirían licencias '
        + 'que ninguna instalación puede verificar. Corregí '
        + 'MVPM_LICENSE_PRIVATE_KEY en Vercel.',
  });
};
