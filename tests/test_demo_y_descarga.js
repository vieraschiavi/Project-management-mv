// © 2026 Martín Viera. Todos los derechos reservados.
//
// La puerta de entrada al producto, ahora que la demo no es pública.
//
// El cambio de criterio: antes la home tenía un botón que bajaba un ZIP con 39
// módulos de `mvpm/` en `.py` legible, y `/api/download-installer` entregaba el
// `.exe` a cualquiera con la URL. Se regalaba el artefacto de ingeniería y no
// quedaba rastro de quién se lo llevaba. Ahora la demo se pide y se muestra en
// vivo, y el instalador se entrega sólo a quien tiene licencia.
//
// Lo que se fija acá, en orden de qué tan caro sale si falla:
//
//  1. Que la descarga NO se entregue sin una licencia válida. Es el punto
//     entero del cambio; si esto se rompe, volvimos al estado anterior sin que
//     nada lo diga.
//  2. Que un pedido de demo no se pierda en silencio. Un pedido perdido es un
//     cliente perdido y no hay forma de enterarse: la persona no vuelve a
//     escribir.
//  3. Que lo que escribe un desconocido no se cuele como HTML en el mail que
//     me llega a mí.

const assert = require('assert');
const crypto = require('crypto');
const path = require('path');

const API = path.resolve(__dirname, '..', 'api');

// Par efímero por corrida, igual que tests/conftest.py: la suite nunca toca
// las claves reales del producto.
(function claves() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  const b64 = (b) => b.toString('base64')
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const pk = privateKey.export({ format: 'der', type: 'pkcs8' });
  const pub = publicKey.export({ format: 'der', type: 'spki' });
  process.env.MVPM_LICENSE_PRIVATE_KEY = b64(pk.subarray(pk.length - 32));
  process.env.MVPM_LICENSE_PUBLIC_KEY = b64(pub.subarray(pub.length - 32));
})();

const { issueLicense } = require(path.join(API, '_license.js'));
const descargar = require(path.join(API, 'download-installer.js'));
const demo = require(path.join(API, 'solicitar-demo.js'));

let pasaron = 0;
function test(nombre, fn) {
  try { fn(); console.log(`  ok   ${nombre}`); pasaron++; }
  catch (e) { console.error(`  FALLA ${nombre}\n       ${e.message}`); process.exitCode = 1; }
}
async function testA(nombre, fn) {
  try { await fn(); console.log(`  ok   ${nombre}`); pasaron++; }
  catch (e) { console.error(`  FALLA ${nombre}\n       ${e.message}`); process.exitCode = 1; }
}

/** Un `res` de mentira que registra lo que la función intentó responder. */
function falsoRes() {
  const r = { code: null, cuerpo: null, cabeceras: null, terminado: false };
  r.status = (c) => { r.code = c; return r; };
  r.json = (b) => { r.cuerpo = b; return r; };
  r.send = (b) => { r.cuerpo = b; return r; };
  r.setHeader = () => {};
  r.writeHead = (c, h) => { r.code = c; r.cabeceras = h; return r; };
  r.end = () => { r.terminado = true; };
  return r;
}

const pedido = (over = {}) => ({
  method: 'POST', headers: {}, query: {},
  body: {
    nombre: 'Ana Pérez', email: 'ana@empresa.com',
    empresa: 'Empresa SA', pais: 'Uruguay', ...over,
  },
});

console.log('descarga del instalador — la puerta cerrada');

(async () => {

  await testA('sin licencia no entrega nada', async () => {
    const res = falsoRes();
    await descargar({ method: 'GET', headers: {}, query: {} }, res);
    assert.strictEqual(res.code, 401);
    assert.strictEqual(res.cabeceras, null, 'redirigió a la descarga sin licencia');
  });

  await testA('una licencia inventada tampoco', async () => {
    const res = falsoRes();
    await descargar({ method: 'GET', headers: {}, query: { token: 'MVPM2.a.b' } }, res);
    assert.strictEqual(res.code, 403);
    assert.strictEqual(res.cabeceras, null);
  });

  await testA('una licencia de OTRO par de claves tampoco', async () => {
    // El caso realista de un intento: alguien firma su propio token con un par
    // que se generó él. La firma es perfecta y la clave no es la nuestra.
    const otro = crypto.generateKeyPairSync('ed25519');
    const der = Buffer.from('302e020100300506032b657004220420', 'hex');
    const pk = otro.privateKey.export({ format: 'der', type: 'pkcs8' });
    const k = crypto.createPrivateKey({
      key: Buffer.concat([der, pk.subarray(pk.length - 32)]),
      format: 'der', type: 'pkcs8' });
    const payload = Buffer.from(JSON.stringify({ plan: 'enterprise' })).toString('base64url');
    const firma = crypto.sign(null, Buffer.from(payload, 'ascii'), k)
      .toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    const res = falsoRes();
    await descargar({ method: 'GET', headers: {}, query: { token: `MVPM2.${payload}.${firma}` } }, res);
    assert.strictEqual(res.code, 403);
    assert.strictEqual(res.cabeceras, null);
  });

  await testA('con licencia válida llega hasta el almacén', async () => {
    // Sin BLOB_READ_WRITE_TOKEN no hay archivo que servir, así que el máximo
    // avance posible es 503. Lo que importa es que YA NO es 401/403: la
    // licencia abrió la puerta y lo que falta es configuración nuestra.
    delete process.env.BLOB_READ_WRITE_TOKEN;
    const res = falsoRes();
    await descargar({
      method: 'GET', headers: {}, query: { token: issueLicense('professional', 'c@e.com', 'mp-1') },
    }, res);
    assert.strictEqual(res.code, 503, `esperaba 503 y dio ${res.code}`);
    assert.strictEqual(res.cuerpo.error, 'no_publicado');
  });

  test('el token se acepta por header, query y cuerpo', () => {
    assert.strictEqual(descargar.tokenDe({ headers: { authorization: 'Bearer abc' }, query: {} }), 'abc');
    assert.strictEqual(descargar.tokenDe({ headers: {}, query: { token: 'def' } }), 'def');
    assert.strictEqual(descargar.tokenDe({ headers: {}, query: {}, body: { token: 'ghi' } }), 'ghi');
    assert.strictEqual(descargar.tokenDe({ headers: {}, query: {} }), '');
  });

  test('el mensaje de rechazo no distingue inventado de vencido', () => {
    // Distinguirlos le diría a quien prueba tokens cuándo va por buen camino.
    const fuente = require('fs').readFileSync(
      path.join(API, 'download-installer.js'), 'utf-8');
    assert.ok(!/vencid|expirad/i.test(fuente.split('licencia_invalida')[1].slice(0, 400)),
      'el mensaje de licencia inválida revela por qué falló');
  });

  console.log('\npedido de demo — validación');

  test('los cuatro campos son obligatorios', () => {
    for (const campo of ['nombre', 'email', 'empresa', 'pais']) {
      const { error } = demo.validar({ ...pedido().body, [campo]: '' });
      assert.strictEqual(error, `falta_${campo}`, `${campo} no se exigió`);
    }
  });

  test('exige nombre COMPLETO, no un apodo', () => {
    // "juan" no sirve para llamar a nadie ni para saber con quién hablás.
    assert.strictEqual(demo.validar({ ...pedido().body, nombre: 'juan' }).error,
                       'nombre_incompleto');
    assert.ok(demo.validar({ ...pedido().body, nombre: 'Juan Pérez' }).datos);
  });

  test('rechaza un email que no es un email', () => {
    for (const malo of ['ana', 'ana@', '@empresa.com', 'ana empresa.com']) {
      assert.strictEqual(demo.validar({ ...pedido().body, email: malo }).error,
                         'email_invalido', `aceptó ${malo}`);
    }
  });

  test('normaliza el email a minúsculas', () => {
    assert.strictEqual(demo.validar({ ...pedido().body, email: 'ANA@Empresa.COM' })
                         .datos.email, 'ana@empresa.com');
  });

  test('recorta campos gigantes en vez de aceptarlos', () => {
    const { datos } = demo.validar({ ...pedido().body, empresa: 'x'.repeat(5000) });
    assert.ok(datos.empresa.length <= 120, `quedó en ${datos.empresa.length}`);
  });

  test('saca saltos de línea de los campos que van al asunto del mail', () => {
    // Con saltos de línea, un nombre puede inyectar cabeceras en un mail mal
    // armado. Se limpian en el origen y no al escribir el asunto.
    const { datos } = demo.validar({
      ...pedido().body, nombre: 'Ana\r\nBcc: otro@ajeno.com Pérez' });
    assert.ok(!/[\r\n]/.test(datos.nombre), 'quedaron saltos de línea en el nombre');
  });

  console.log('\npedido de demo — lo que llega a mi bandeja');

  test('escapa el HTML de lo que escribe un desconocido', () => {
    const s = demo.escapar('<img src=x onerror="alert(1)"> & \'comillas\'');
    assert.ok(!s.includes('<img'), 'pasó una etiqueta HTML');
    assert.ok(!s.includes('"'), 'pasaron comillas dobles sin escapar');
    assert.ok(s.includes('&amp;'), 'no escapó el ampersand');
  });

  await testA('sin proveedor de mail Y sin almacén, avisa que se perdió', async () => {
    // El caso peor: los dos caminos caídos. Agradecerle a alguien por un
    // pedido que nadie va a leer es la falla más cara de todo el flujo,
    // porque la persona no vuelve a escribir.
    delete process.env.RESEND_API_KEY;
    delete process.env.DEMO_FROM_EMAIL;
    delete process.env.BLOB_READ_WRITE_TOKEN;
    const errores = [];
    const orig = console.error;
    console.error = (...a) => errores.push(a.join(' '));
    const res = falsoRes();
    try { await demo(pedido(), res); } finally { console.error = orig; }
    assert.strictEqual(res.code, 503, `respondió ${res.code}, no avisó del problema`);
    assert.strictEqual(res.cuerpo.escribinos, demo.DESTINO);
    assert.ok(errores.some((e) => e.includes('PEDIDO DE DEMO PERDIDO')),
              'no dejó rastro en el log del servidor');
  });

  await testA('un GET no crea un pedido', async () => {
    const res = falsoRes();
    await demo({ ...pedido(), method: 'GET' }, res);
    assert.strictEqual(res.code, 405);
  });

  await testA('un cuerpo que es JSON roto no revienta', async () => {
    const res = falsoRes();
    await demo({ method: 'POST', headers: {}, query: {}, body: '{no es json' }, res);
    assert.strictEqual(res.code, 400);
  });

  test('el endpoint no conoce ninguna URL de descarga', () => {
    // La garantía estructural del cambio: por más que alguien se equivoque
    // más adelante, esta función no PUEDE entregar el producto.
    const fuente = require('fs').readFileSync(
      path.join(API, 'solicitar-demo.js'), 'utf-8');
    for (const pista of ['installers/', '.exe', 'download-installer', 'blob.vercel']) {
      assert.ok(!fuente.includes(pista),
                `solicitar-demo.js menciona "${pista}": podría filtrar el producto`);
    }
  });

  if (!process.exitCode) console.log(`\ntodos los tests de demo y descarga pasaron (${pasaron})`);
})();
