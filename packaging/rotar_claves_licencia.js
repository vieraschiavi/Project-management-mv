// © 2026 Martín Viera. Todos los derechos reservados.
//
// Rota el par de claves de licencias SIN que la clave privada pase por manos
// humanas, por un chat, ni por un log.
//
// Lo corre `.github/workflows/rotar_claves_licencia.yml` con un botón. Hace,
// en este orden:
//
//   1. genera un par Ed25519 nuevo;
//   2. escribe la PRIVADA en las variables de entorno de Vercel por API;
//   3. pega la PÚBLICA en `mvpm/licensing.py` y en `api/_license.js`;
//   4. borra `MVPM_LICENSE_PUBLIC_KEY` de Vercel si existía.
//
// El paso 4 no es limpieza cosmética. `api/_license.js` prefiere esa variable
// por encima de la constante embebida, así que mientras exista, la comprobación
// que impide emitir licencias que ningún programa puede abrir se compara contra
// sí misma y no detecta nada. Sin la variable, la única autoridad es la
// constante que viaja compilada en el instalador — que es la que importa.
//
// La privada nunca se imprime. No se escribe en ningún archivo del repositorio,
// no va al stdout del workflow y no queda en el resumen: sale de este proceso
// únicamente por HTTPS hacia la API de Vercel.
//
// ## Cuándo se puede rotar sin romper nada
//
// Rotar invalida TODA licencia emitida con la clave vieja. Es gratis mientras
// no se haya emitido ninguna —y hoy es el caso: producción nunca tuvo clave
// privada configurada, así que `verify-payment` respondía 500 y nadie recibió
// un token que funcione. Después de la primera venta, rotar tiene costo real:
// hay que reemitir la licencia de cada cliente.

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const RAIZ = path.resolve(__dirname, '..');
const ARCHIVO_PY = path.join(RAIZ, 'mvpm', 'licensing.py');
const ARCHIVO_JS = path.join(RAIZ, 'api', '_license.js');

const API = 'https://api.vercel.com';

function b64url(buf) {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** Par Ed25519 nuevo, en los 32 bytes crudos que usan las dos implementaciones. */
function generarPar() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  const pkcs8 = privateKey.export({ format: 'der', type: 'pkcs8' });
  const spki = publicKey.export({ format: 'der', type: 'spki' });
  // Los últimos 32 bytes son la clave; lo anterior es el encabezado DER.
  return {
    privada: b64url(pkcs8.subarray(pkcs8.length - 32)),
    publica: b64url(spki.subarray(spki.length - 32)),
  };
}

async function vercel(metodo, ruta, token, cuerpo) {
  const r = await fetch(`${API}${ruta}`, {
    method: metodo,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  const texto = await r.text();
  let datos = null;
  try { datos = texto ? JSON.parse(texto) : null; } catch { /* respuesta no-JSON */ }
  if (!r.ok) {
    // El mensaje de error de Vercel nunca incluye el valor enviado, pero por
    // las dudas se recorta: un 400 no puede terminar filtrando la clave al log.
    const motivo = (datos && datos.error && datos.error.message) || r.statusText;
    throw new Error(`Vercel ${metodo} ${ruta} -> ${r.status}: ${String(motivo).slice(0, 200)}`);
  }
  return datos;
}

/** Borra toda variable con ese nombre, en cualquier entorno. Idempotente. */
async function borrarVariable(nombre, { token, projectId, teamId }) {
  const q = teamId ? `?teamId=${teamId}` : '';
  const actuales = await vercel('GET', `/v9/projects/${projectId}/env${q}`, token);
  const iguales = (actuales.envs || []).filter((e) => e.key === nombre);
  for (const e of iguales) {
    await vercel('DELETE', `/v9/projects/${projectId}/env/${e.id}${q}`, token);
  }
  return iguales.length;
}

async function cargarPrivadaEnVercel(privada, config) {
  const q = config.teamId ? `?teamId=${config.teamId}` : '';
  // Se borra antes de crear: la API rechaza una clave duplicada en el mismo
  // entorno, y un upsert parcial dejaría producción con la clave vieja y
  // preview con la nueva — el peor de los dos mundos, porque el checkout
  // seguiría emitiendo tokens que el programa no abre.
  const borradas = await borrarVariable('MVPM_LICENSE_PRIVATE_KEY', config);
  await vercel('POST', `/v10/projects/${config.projectId}/env${q}`, config.token, {
    key: 'MVPM_LICENSE_PRIVATE_KEY',
    value: privada,
    type: 'encrypted',
    target: ['production', 'preview', 'development'],
  });
  return borradas;
}

function pegarPublica(publica) {
  const py = fs.readFileSync(ARCHIVO_PY, 'utf-8');
  const pyNuevo = py.replace(
    /^CLAVE_PUBLICA_EMBEBIDA = ".*"$/m, `CLAVE_PUBLICA_EMBEBIDA = "${publica}"`);
  if (pyNuevo === py) {
    throw new Error(`No encontré CLAVE_PUBLICA_EMBEBIDA en ${ARCHIVO_PY}`);
  }

  const js = fs.readFileSync(ARCHIVO_JS, 'utf-8');
  const jsNuevo = js.replace(
    /^const CLAVE_PUBLICA_EMBEBIDA = '.*';$/m,
    `const CLAVE_PUBLICA_EMBEBIDA = '${publica}';`);
  if (jsNuevo === js) {
    throw new Error(`No encontré CLAVE_PUBLICA_EMBEBIDA en ${ARCHIVO_JS}`);
  }

  // Se escriben los dos o ninguno: si el programa y el servidor quedaran con
  // públicas distintas, el servidor emitiría licencias que el programa rechaza,
  // que es exactamente lo que esta rotación viene a arreglar.
  fs.writeFileSync(ARCHIVO_PY, pyNuevo, 'utf-8');
  fs.writeFileSync(ARCHIVO_JS, jsNuevo, 'utf-8');
}

/** Comprueba, antes de tocar nada, que la privada nueva firme algo que la
 *  pública nueva verifique. Si esto fallara, el par no serviría y no tiene
 *  sentido escribirlo en ningún lado. */
function comprobarElPar({ privada, publica }) {
  const DER_PRIV = Buffer.from('302e020100300506032b657004220420', 'hex');
  const DER_PUB = Buffer.from('302a300506032b6570032100', 'hex');
  const dec = (s) => {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    return Buffer.from(s, 'base64');
  };
  const k = crypto.createPrivateKey({
    key: Buffer.concat([DER_PRIV, dec(privada)]), format: 'der', type: 'pkcs8' });
  const p = crypto.createPublicKey({
    key: Buffer.concat([DER_PUB, dec(publica)]), format: 'der', type: 'spki' });
  const mensaje = Buffer.from('comprobacion-de-par', 'ascii');
  if (!crypto.verify(null, mensaje, p, crypto.sign(null, mensaje, k))) {
    throw new Error('El par generado no se verifica a sí mismo. Abortado.');
  }
}

async function main() {
  const token = process.env.VERCEL_TOKEN;
  const projectId = process.env.VERCEL_PROJECT_ID;
  const teamId = process.env.VERCEL_TEAM_ID || '';
  if (!token || !projectId) {
    console.error(
      'Faltan VERCEL_TOKEN y/o VERCEL_PROJECT_ID.\n'
      + 'Se cargan una sola vez en GitHub -> Settings -> Secrets and variables\n'
      + '-> Actions. Ver owner/PUESTA_EN_PRODUCCION.md.');
    process.exit(2);
  }

  const par = generarPar();
  comprobarElPar(par);
  console.log('Par Ed25519 generado y comprobado.');
  console.log(`  Clave pública (NO es secreta): ${par.publica}`);

  const config = { token, projectId, teamId };
  const reemplazadas = await cargarPrivadaEnVercel(par.privada, config);
  console.log(`Clave privada cargada en Vercel (production, preview, development).`
    + ` Variables anteriores reemplazadas: ${reemplazadas}.`);

  const publicasBorradas = await borrarVariable('MVPM_LICENSE_PUBLIC_KEY', config);
  if (publicasBorradas) {
    console.log(`Se borró MVPM_LICENSE_PUBLIC_KEY (${publicasBorradas}):`
      + ' pisaba la clave embebida y desactivaba la comprobación de emisión.');
  }

  pegarPublica(par.publica);
  console.log('Clave pública pegada en mvpm/licensing.py y api/_license.js.');
  console.log('\nLa clave PRIVADA no se imprimió en ningún momento y no quedó');
  console.log('en ningún archivo: viajó sólo por HTTPS hacia Vercel.');
}

if (require.main === module) {
  main().catch((e) => { console.error(String(e.message || e)); process.exit(1); });
}

module.exports = { generarPar, comprobarElPar, pegarPublica };
