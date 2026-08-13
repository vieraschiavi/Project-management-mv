// © 2026 Martín Viera. Todos los derechos reservados.
// Tests del checkout de MercadoPago (api/checkout.js).
//
// Es el endpoint que genera el link de pago: si acepta un plan que no existe,
// cobra el monto equivocado o filtra el access token, se pierde plata o se
// rompe la venta. Se corre con `node tests/test_checkout.js`.

process.env.MP_CURRENCY = 'UYU';
process.env.MP_TASA_UYU = '40';

const assert = require('assert');

let fallos = 0;
async function test(nombre, fn) {
  try { await fn(); console.log(`  ok   ${nombre}`); }
  catch (e) { fallos++; console.error(`  FALLA ${nombre}\n         ${e.message}`); }
}

function fakeRes() {
  const res = { statusCode: null, body: null, headers: {} };
  res.status = (c) => { res.statusCode = c; return res; };
  res.json = (b) => { res.body = b; return res; };
  res.setHeader = (k, v) => { res.headers[k] = v; };
  return res;
}

/** Pide el módulo de cero, para que relea las env vars y resetee el rate limit. */
function cargarCheckout() {
  for (const m of ['../api/checkout', '../api/_planes', '../api/_ratelimit']) {
    delete require.cache[require.resolve(m)];
  }
  return require('../api/checkout');
}

/** Request con IP propia, así cada test arranca con su cubo de rate limit. */
let n = 0;
function req(body, metodo = 'POST') {
  n += 1;
  return { method: metodo, body, headers: { 'x-forwarded-for': `10.0.0.${n}` } };
}

(async () => {
  console.log('checkout.js — validación de entrada');

  await test('rechaza un método que no sea POST', async () => {
    const h = cargarCheckout();
    const res = fakeRes();
    await h(req({ plan: 'professional' }, 'GET'), res);
    assert.strictEqual(res.statusCode, 405);
  });

  await test('rechaza un plan que no existe', async () => {
    const h = cargarCheckout();
    const res = fakeRes();
    await h(req({ plan: 'plan_trucho' }), res);
    assert.strictEqual(res.statusCode, 400);
    assert.strictEqual(res.body.error, 'plan_invalido');
  });

  await test('rechaza enterprise: no se vende online, se cotiza por proyecto', async () => {
    const h = cargarCheckout();
    const res = fakeRes();
    await h(req({ plan: 'enterprise' }), res);
    assert.strictEqual(res.statusCode, 400);
  });

  await test('rechaza demo: es gratis, no tiene checkout', async () => {
    const h = cargarCheckout();
    const res = fakeRes();
    await h(req({ plan: 'demo' }), res);
    assert.strictEqual(res.statusCode, 400);
  });

  await test('rechaza un body vacío o sin plan', async () => {
    const h = cargarCheckout();
    for (const body of [{}, null, undefined, { plan: '' }]) {
      const res = fakeRes();
      await h(req(body), res);
      assert.strictEqual(res.statusCode, 400, `body ${JSON.stringify(body)}`);
    }
  });

  await test('no revienta con un body que es JSON inválido', async () => {
    const h = cargarCheckout();
    const res = fakeRes();
    await h(req('{esto no es json'), res);
    assert.strictEqual(res.statusCode, 400);
  });

  await test('normaliza mayúsculas en el plan', async () => {
    const h = cargarCheckout();
    const res = fakeRes();
    await h(req({ plan: 'PROFESSIONAL' }), res);
    // No es 400: el plan se reconoce. Sin MP_ACCESS_TOKEN da 503, que es otra cosa.
    assert.notStrictEqual(res.statusCode, 400);
  });

  console.log('\ncheckout.js — sin medio de pago configurado');

  await test('sin token ni link fijo responde 503, no 500', async () => {
    delete process.env.MP_ACCESS_TOKEN;
    delete process.env.MP_LINK_PROFESSIONAL;
    const h = cargarCheckout();
    const res = fakeRes();
    await h(req({ plan: 'professional' }), res);
    assert.strictEqual(res.statusCode, 503);
    assert.strictEqual(res.body.error, 'medio_pago_no_configurado');
  });

  await test('sin token pero con link fijo, devuelve el link', async () => {
    delete process.env.MP_ACCESS_TOKEN;
    process.env.MP_LINK_PROFESSIONAL = 'https://mpago.la/link-fijo';
    const h = cargarCheckout();
    const res = fakeRes();
    await h(req({ plan: 'professional' }), res);
    assert.strictEqual(res.statusCode, 200);
    assert.strictEqual(res.body.url, 'https://mpago.la/link-fijo');
    assert.strictEqual(res.body.modo, 'link_fijo');
    delete process.env.MP_LINK_PROFESSIONAL;
  });

  console.log('\ncheckout.js — montos y datos que se mandan a MercadoPago');

  await test('cobra el monto del plan convertido a pesos, no los dólares', async () => {
    process.env.MP_ACCESS_TOKEN = 'token-de-prueba';
    const h = cargarCheckout();
    let enviado = null;
    global.fetch = async (url, opts) => {
      enviado = { url, body: JSON.parse(opts.body) };
      return { ok: true, json: async () => ({ init_point: 'https://mp/checkout' }) };
    };
    const res = fakeRes();
    await h(req({ plan: 'professional' }), res);
    assert.strictEqual(res.statusCode, 200);
    // professional = US$9 · tasa 40 => $U 360 mensuales, no 9.
    assert.strictEqual(enviado.body.auto_recurring.transaction_amount, 360);
    assert.strictEqual(enviado.body.auto_recurring.currency_id, 'UYU');
    assert.strictEqual(enviado.body.auto_recurring.frequency_type, 'months');
    delete process.env.MP_ACCESS_TOKEN;
  });

  await test('el plan anual cobra US$90 → $U 3600 en un pago único', async () => {
    process.env.MP_ACCESS_TOKEN = 'token-de-prueba';
    const h = cargarCheckout();
    let enviado = null;
    global.fetch = async (url, opts) => {
      enviado = { url, body: JSON.parse(opts.body) };
      return { ok: true, json: async () => ({ init_point: 'https://mp/checkout' }) };
    };
    const res = fakeRes();
    await h(req({ plan: 'professional_anual' }), res);
    assert.strictEqual(res.statusCode, 200);
    assert.strictEqual(enviado.body.items[0].unit_price, 3600);
    assert.strictEqual(enviado.body.items[0].currency_id, 'UYU');
    // metadata.plan es lo que verify-payment usa para NO confiar en el query string.
    assert.strictEqual(enviado.body.metadata.plan, 'professional_anual');
    delete process.env.MP_ACCESS_TOKEN;
  });

  await test('manda el access token por header, nunca en el cuerpo ni en la URL', async () => {
    process.env.MP_ACCESS_TOKEN = 'token-super-secreto';
    const h = cargarCheckout();
    let capturado = null;
    global.fetch = async (url, opts) => {
      capturado = { url, opts };
      return { ok: true, json: async () => ({ init_point: 'https://mp/checkout' }) };
    };
    const res = fakeRes();
    await h(req({ plan: 'professional' }), res);
    assert.ok(capturado.opts.headers.Authorization.includes('token-super-secreto'));
    assert.ok(!capturado.url.includes('token-super-secreto'), 'no puede ir en la URL');
    assert.ok(!capturado.opts.body.includes('token-super-secreto'), 'no puede ir en el body');
    // Y sobre todo: no puede volver al navegador.
    assert.ok(!JSON.stringify(res.body).includes('token-super-secreto'));
    delete process.env.MP_ACCESS_TOKEN;
  });

  await test('si MercadoPago falla, no filtra el detalle del error al cliente', async () => {
    process.env.MP_ACCESS_TOKEN = 'token-de-prueba';
    const h = cargarCheckout();
    global.fetch = async () => ({
      ok: false,
      json: async () => ({ message: 'detalle interno con el token adentro' }),
    });
    const res = fakeRes();
    await h(req({ plan: 'professional_anual' }), res);
    assert.strictEqual(res.statusCode, 502);
    assert.strictEqual(res.body.error, 'mercadopago');
    assert.ok(!JSON.stringify(res.body).includes('detalle interno'));
    delete process.env.MP_ACCESS_TOKEN;
  });

  await test('si fetch lanza, responde 500 controlado y no propaga la excepción', async () => {
    process.env.MP_ACCESS_TOKEN = 'token-de-prueba';
    const h = cargarCheckout();
    global.fetch = async () => { throw new Error('red caída'); };
    const res = fakeRes();
    await h(req({ plan: 'professional_anual' }), res);
    assert.strictEqual(res.statusCode, 500);
    assert.ok(!JSON.stringify(res.body).includes('red caída'));
    delete process.env.MP_ACCESS_TOKEN;
  });

  console.log('\ncheckout.js — rate limiting');

  await test('corta al pasarse del límite por IP', async () => {
    const h = cargarCheckout();
    const mismaIp = { method: 'POST', body: { plan: 'plan_trucho' },
                      headers: { 'x-forwarded-for': '198.51.100.7' } };
    let limitado = false;
    for (let i = 0; i < 15; i++) {
      const res = fakeRes();
      await h(mismaIp, res);
      if (res.statusCode === 429) { limitado = true; break; }
    }
    assert.ok(limitado, 'después de 10 intentos seguidos debería devolver 429');
  });

  await test('el 429 dice cuánto esperar', async () => {
    const h = cargarCheckout();
    const mismaIp = { method: 'POST', body: { plan: 'plan_trucho' },
                      headers: { 'x-forwarded-for': '198.51.100.8' } };
    let res;
    for (let i = 0; i < 15; i++) {
      res = fakeRes();
      await h(mismaIp, res);
      if (res.statusCode === 429) break;
    }
    assert.strictEqual(res.statusCode, 429);
    assert.ok(res.headers['Retry-After'], 'falta el header Retry-After');
    assert.ok(res.body.reintentar_en_segundos > 0);
  });

  if (fallos) { console.error(`\n${fallos} test(s) fallaron`); process.exit(1); }
  console.log('\ntodos los tests de checkout pasaron');
})();
