// © 2026 Martín Viera. Todos los derechos reservados.
// Tests de la emisión y verificación de licencias (api/_license.js).
//
// Es el módulo que decide quién tiene acceso pago, así que su firma es lo que
// separa un cliente que pagó de cualquiera que sepa armar un JSON. Se corre con
// `node tests/test_licencias.js`; el workflow tests.yml lo ejecuta en cada push.

const assert = require('assert');
const crypto = require('crypto');

// Par Ed25519 efímero para la corrida. Las claves reales no están en el repo
// (la privada vive como variable de entorno en Vercel), y no deben estarlo.
function parDeClaves() {
  const { privateKey } = crypto.generateKeyPairSync('ed25519');
  // El DER PKCS#8 de una Ed25519 son 48 bytes: 16 de encabezado fijo + los 32
  // de la semilla, que es el formato crudo que usan _license.js y Python.
  const semilla = privateKey.export({ format: 'der', type: 'pkcs8' }).subarray(16);
  return semilla.toString('base64url');
}

process.env.MVPM_LICENSE_PRIVATE_KEY = parDeClaves();

const { PLANES, issueLicense, verifyLicense, FIRMAS_REVOCADAS } = require('../api/_license');

let fallos = 0;
function test(nombre, fn) {
  try { fn(); console.log(`  ok   ${nombre}`); }
  catch (e) { fallos++; console.error(`  FALLA ${nombre}\n         ${e.message}`); }
}

console.log('_license.js — emisión');

test('emite un token con el formato MVPM2.<payload>.<firma>', () => {
  const t = issueLicense('professional', 'cliente@ejemplo.com');
  const partes = t.split('.');
  assert.strictEqual(partes.length, 3);
  assert.strictEqual(partes[0], 'MVPM2');
  assert.ok(partes[1].length > 0 && partes[2].length > 0);
});

test('el payload lleva plan, email, payment_id y el cupo del plan', () => {
  const t = issueLicense('professional', 'cliente@ejemplo.com', 'pago-123');
  const p = verifyLicense(t);
  assert.strictEqual(p.plan, 'professional');
  assert.strictEqual(p.email, 'cliente@ejemplo.com');
  assert.strictEqual(p.payment_id, 'pago-123');
  assert.strictEqual(p.cupo_mensual_ia, PLANES.professional.cupo_mensual_ia);
});

test('enterprise se emite con cupo de IA ilimitado (null)', () => {
  const p = verifyLicense(issueLicense('enterprise', 'grande@ejemplo.com'));
  assert.strictEqual(p.cupo_mensual_ia, null);
});

test('rechaza un plan que no existe en el catálogo', () => {
  assert.throws(() => issueLicense('plan_inventado', 'x@y.com'), /Plan desconocido/);
});

test('el token no lleva la clave privada adentro', () => {
  const t = issueLicense('professional', 'cliente@ejemplo.com');
  assert.ok(!t.includes(process.env.MVPM_LICENSE_PRIVATE_KEY),
            'la clave privada de firma no puede viajar en el token');
  const crudo = Buffer.from(t.split('.')[1], 'base64').toString();
  assert.ok(!crudo.includes(process.env.MVPM_LICENSE_PRIVATE_KEY));
});

test('el payload es legible (no está cifrado) — es firmado, no secreto', () => {
  // Se afirma a propósito: el esquema garantiza INTEGRIDAD, no confidencialidad.
  // Si alguna vez hiciera falta ocultar el email, hay que cifrar, no firmar.
  const t = issueLicense('professional', 'cliente@ejemplo.com');
  const crudo = Buffer.from(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'),
                            'base64').toString();
  assert.ok(crudo.includes('cliente@ejemplo.com'));
});

console.log('\n_license.js — verificación');

test('un token recién emitido verifica', () => {
  assert.ok(verifyLicense(issueLicense('professional', 'a@b.com')));
});

test('RECHAZA un payload manipulado (subir de plan sin re-firmar)', () => {
  const t = issueLicense('professional', 'a@b.com');
  const [pref, payloadB64, firma] = t.split('.');
  const payload = JSON.parse(Buffer.from(payloadB64.replace(/-/g, '+').replace(/_/g, '/'),
                                         'base64').toString());
  payload.plan = 'enterprise';
  payload.cupo_mensual_ia = null;
  const falsificado = Buffer.from(JSON.stringify(payload)).toString('base64')
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  assert.strictEqual(verifyLicense(`${pref}.${falsificado}.${firma}`), null);
});

test('RECHAZA una firma alterada', () => {
  const t = issueLicense('professional', 'a@b.com');
  const [pref, payloadB64, firma] = t.split('.');
  const otra = (firma[0] === 'A' ? 'B' : 'A') + firma.slice(1);
  assert.strictEqual(verifyLicense(`${pref}.${payloadB64}.${otra}`), null);
});

test('RECHAZA un token firmado con otra clave privada', () => {
  // Es el ataque que el esquema asimétrico tiene que frenar: cualquiera puede
  // generarse un par de claves, pero sólo la privada del dueño produce firmas
  // que la pública embebida en el programa acepta.
  const original = process.env.MVPM_LICENSE_PRIVATE_KEY;
  process.env.MVPM_LICENSE_PRIVATE_KEY = parDeClaves();
  delete require.cache[require.resolve('../api/_license')];
  const otroModulo = require('../api/_license');
  const ajeno = otroModulo.issueLicense('professional', 'a@b.com');

  process.env.MVPM_LICENSE_PRIVATE_KEY = original;
  delete require.cache[require.resolve('../api/_license')];
  const nuestro = require('../api/_license');
  assert.strictEqual(nuestro.verifyLicense(ajeno), null,
                     'un token de otra instalación no debe validar acá');
});

test('RECHAZA un prefijo que no es MVPM2', () => {
  const t = issueLicense('professional', 'a@b.com');
  assert.strictEqual(verifyLicense('OTRO.' + t.split('.').slice(1).join('.')), null);
});

test('RECHAZA basura sin romperse', () => {
  for (const basura of ['', 'no-es-un-token', 'a.b', 'a.b.c.d', 'MVPM2..', 'MVPM2.@@@.###']) {
    assert.strictEqual(verifyLicense(basura), null, `debería rechazar: ${basura}`);
  }
});

test('RECHAZA null/undefined sin lanzar', () => {
  assert.strictEqual(verifyLicense(null), null);
  assert.strictEqual(verifyLicense(undefined), null);
});

console.log('\n_license.js — configuración');

test('falla explícito si no hay clave privada configurada', () => {
  const original = process.env.MVPM_LICENSE_PRIVATE_KEY;
  delete process.env.MVPM_LICENSE_PRIVATE_KEY;
  delete require.cache[require.resolve('../api/_license')];
  const sinClave = require('../api/_license');
  // Emitir sin la clave del dueño haría licencias que no validan en ninguna
  // PC: mejor reventar que entregarle al que pagó algo inservible.
  assert.throws(() => sinClave.issueLicense('professional', 'a@b.com'),
                /MVPM_LICENSE_PRIVATE_KEY/);
  process.env.MVPM_LICENSE_PRIVATE_KEY = original;
  delete require.cache[require.resolve('../api/_license')];
});

test('RECHAZA una clave privada que no mide 32 bytes', () => {
  const original = process.env.MVPM_LICENSE_PRIVATE_KEY;
  process.env.MVPM_LICENSE_PRIVATE_KEY = Buffer.from('corta').toString('base64url');
  delete require.cache[require.resolve('../api/_license')];
  const malConfigurado = require('../api/_license');
  assert.throws(() => malConfigurado.issueLicense('professional', 'a@b.com'),
                /32 bytes/);
  process.env.MVPM_LICENSE_PRIVATE_KEY = original;
  delete require.cache[require.resolve('../api/_license')];
});

test('el catálogo de planes coincide con el de Python (mvpm/licensing.py)', () => {
  // Los dos lados emiten y verifican el MISMO token: si los cupos se
  // desalinean, un cliente ve un límite distinto según quién lo atienda.
  const esperados = ['demo', 'professional', 'professional_anual', 'enterprise'];
  assert.deepStrictEqual(Object.keys(PLANES).sort(), esperados.sort());
  assert.strictEqual(PLANES.demo.cupo_mensual_ia, 20);
  assert.strictEqual(PLANES.professional.cupo_mensual_ia, 1000);
  assert.strictEqual(PLANES.professional_anual.cupo_mensual_ia, 1000);
  assert.strictEqual(PLANES.enterprise.cupo_mensual_ia, null);
});

test('la lista de revocados dice lo mismo que la de Python', () => {
  // Las dos mitades del mismo esquema. Si se desincronizan, el servidor sigue
  // aceptando un token que el programa ya rechaza (o al reves), y la revocacion
  // deja de significar nada. La lista existe porque packaging/OWNER_EDITION
  // quedo versionado en un repo publico con una licencia enterprise adentro.
  const fs = require('fs');
  const path = require('path');
  const py = fs.readFileSync(
    path.join(__dirname, '..', 'mvpm', 'licensing.py'), 'utf-8');
  const bloque = py.match(/FIRMAS_REVOCADAS = frozenset\(\{([\s\S]*?)\}\)/);
  assert.ok(bloque, 'no encontre FIRMAS_REVOCADAS en mvpm/licensing.py');
  const enPython = new Set(
    [...bloque[1].matchAll(/"([A-Za-z0-9_-]{40,})"/g)].map((m) => m[1]));

  assert.ok(enPython.size > 0, 'FIRMAS_REVOCADAS quedo vacia en Python');
  assert.deepStrictEqual([...FIRMAS_REVOCADAS].sort(), [...enPython].sort());
});

test('un token revocado se rechaza aunque la firma sea impecable', () => {
  const token = issueLicense('enterprise', 'dueno@ejemplo.com');
  assert.ok(verifyLicense(token), 'el token recien emitido deberia valer');

  const firma = token.split('.')[2];
  FIRMAS_REVOCADAS.add(firma);
  try {
    assert.strictEqual(verifyLicense(token), null);
  } finally {
    FIRMAS_REVOCADAS.delete(firma);
  }
});

if (fallos) { console.error(`\n${fallos} test(s) fallaron`); process.exit(1); }
console.log('\ntodos los tests de licencias pasaron');
