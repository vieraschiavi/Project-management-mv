// Tests de la emisión de licencias tras un pago (api/verify-payment.js).
//
// Se corre con `node tests/test_verify_payment.js` (sin framework: es el único
// test de JS del repo y no justifica sumar una dependencia). El workflow
// .github/workflows/tests.yml lo ejecuta en cada push.
//
// Lo que cubre es el agujero que tenía este endpoint: el plan a emitir salía
// del query string sin validar, así que un pago real y aprobado del plan más
// barato podía canjearse por una licencia de un plan superior con sólo
// cambiar la URL.

// Par Ed25519 efímero: las licencias se firman con clave privada del dueño,
// que no está en el repo. Sin esto, issueLicense() revienta y todo responde 500.
process.env.MVPM_LICENSE_PRIVATE_KEY = require('crypto')
  .generateKeyPairSync('ed25519').privateKey
  .export({ format: 'der', type: 'pkcs8' }).subarray(16).toString('base64url');
process.env.MP_ACCESS_TOKEN = 'token-de-prueba';
process.env.MP_CURRENCY = 'UYU';
process.env.MP_TASA_UYU = '40';

const assert = require('assert');
const handler = require('../api/verify-payment');
const { verifyLicense } = require('../api/_license');

let fallos = 0;
function test(nombre, fn) {
  return fn().then(
    () => console.log(`  ok   ${nombre}`),
    (e) => { fallos++; console.error(`  FALLA ${nombre}\n         ${e.message}`); }
  );
}

/** Respuesta falsa de la API de MercadoPago para un pago dado. */
function mockMercadoPago({ status = 'approved', amount = 360, metadata = {} } = {}) {
  global.fetch = async () => ({
    ok: true,
    json: async () => ({
      id: 12345, status, transaction_amount: amount,
      metadata, payer: { email: 'cliente@ejemplo.com' },
    }),
  });
}

function fakeRes() {
  const res = { statusCode: null, body: null };
  res.status = (c) => { res.statusCode = c; return res; };
  res.json = (b) => { res.body = b; return res; };
  return res;
}

async function llamar(query) {
  const res = fakeRes();
  await handler({ query }, res);
  return res;
}

(async () => {
  console.log('verify-payment.js');

  await test('emite Professional con un pago aprobado de $U360', async () => {
    mockMercadoPago({ amount: 360, metadata: { plan: 'professional' } });
    const res = await llamar({ payment_id: '12345', plan: 'professional' });
    assert.strictEqual(res.statusCode, 200);
    assert.strictEqual(res.body.plan, 'professional');
    assert.strictEqual(verifyLicense(res.body.license_token).plan, 'professional');
  });

  await test('RECHAZA enterprise pedido por query string (no es vendible online)', async () => {
    mockMercadoPago({ amount: 360, metadata: { plan: 'professional' } });
    const res = await llamar({ payment_id: '12345', plan: 'enterprise' });
    assert.strictEqual(res.statusCode, 400, `esperaba 400 y dio ${res.statusCode}`);
    assert.ok(!res.body.license_token, 'no debe emitir ninguna licencia');
  });

  await test('RECHAZA el plan anual si sólo se pagó el mensual', async () => {
    // Pago real y aprobado de Professional ($U360) reclamando el anual ($U3600).
    mockMercadoPago({ amount: 360, metadata: {} });
    const res = await llamar({ payment_id: '12345', plan: 'professional_anual' });
    assert.strictEqual(res.statusCode, 402, `esperaba 402 y dio ${res.statusCode}`);
    assert.ok(!res.body.license_token, 'no debe emitir ninguna licencia');
  });

  await test('el plan del pago (metadata) le gana al del query string', async () => {
    mockMercadoPago({ amount: 3600, metadata: { plan: 'professional_anual' } });
    const res = await llamar({ payment_id: '12345', plan: 'professional' });
    assert.strictEqual(res.statusCode, 200);
    assert.strictEqual(res.body.plan, 'professional_anual');
  });

  await test('no emite nada si el pago no está aprobado', async () => {
    mockMercadoPago({ status: 'pending', amount: 360 });
    const res = await llamar({ payment_id: '12345', plan: 'professional' });
    assert.strictEqual(res.statusCode, 402);
    assert.ok(!res.body.license_token);
  });

  await test('exige payment_id', async () => {
    const res = await llamar({ plan: 'professional' });
    assert.strictEqual(res.statusCode, 400);
  });

  await test('tolera una baja del tipo de cambio dentro del margen', async () => {
    // $U320 por un plan de $U360 esperado: -11%, dentro del 15% de margen.
    mockMercadoPago({ amount: 320, metadata: { plan: 'professional' } });
    const res = await llamar({ payment_id: '12345', plan: 'professional' });
    assert.strictEqual(res.statusCode, 200);
  });

  if (fallos) { console.error(`\n${fallos} test(s) fallaron`); process.exit(1); }
  console.log('\ntodos los tests de verify-payment pasaron');
})();
