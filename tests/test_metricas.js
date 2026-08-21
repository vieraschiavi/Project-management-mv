// © 2026 Martín Viera. Todos los derechos reservados.
//
// api/_metricas.js — el tablero del dueño.
//
// Un tablero de plata falla distinto que el resto del código: no tira error,
// muestra un número. Si el número está mal, la decisión que se toma mirándolo
// está mal, y nada avisa. Por eso lo que se fija acá no es que "devuelva
// algo", sino que:
//
//  1. el neto sea el que informa MercadoPago y NUNCA una estimación propia;
//  2. un pago sin neto informado se cuente como faltante y no como cero
//     disfrazado de dato;
//  3. un cliente que pagó y no tiene licencia aparezca — es la única cifra de
//     todo el tablero que hay que mirar el mismo día.

const assert = require('assert');
const path = require('path');

const { resumir, pagosAprobados, mesDe } =
  require(path.resolve(__dirname, '..', 'api', '_metricas.js'));

let pasaron = 0;
function test(nombre, fn) {
  try {
    fn();
    console.log(`  ok   ${nombre}`);
    pasaron++;
  } catch (e) {
    console.error(`  FALLA ${nombre}\n       ${e.message}`);
    process.exitCode = 1;
  }
}
async function testAsync(nombre, fn) {
  try {
    await fn();
    console.log(`  ok   ${nombre}`);
    pasaron++;
  } catch (e) {
    console.error(`  FALLA ${nombre}\n       ${e.message}`);
    process.exitCode = 1;
  }
}

function pago(over = {}) {
  return {
    id: over.id || 1,
    status: 'approved',
    date_approved: over.fecha || '2026-08-15T12:00:00.000-04:00',
    transaction_amount: over.bruto === undefined ? 360 : over.bruto,
    currency_id: 'UYU',
    payer: { email: over.email || 'cliente@ejemplo.com' },
    metadata: { plan: over.plan || 'professional' },
    transaction_details: over.neto === null ? {}
      : { net_received_amount: over.neto === undefined ? 330 : over.neto },
  };
}

console.log('metricas — el dinero');

test('el neto es el de MercadoPago, no una comisión inventada', () => {
  const r = resumir({ pagos: [pago({ bruto: 360, neto: 328.5 })] });
  assert.strictEqual(r.dinero.bruto, 360);
  assert.strictEqual(r.dinero.neto_recibido, 328.5);
  assert.strictEqual(r.dinero.comision_mercadopago, 31.5);
});

test('la comisión sale de la resta y no de un porcentaje fijo', () => {
  // Dos pagos del mismo monto con netos distintos —pasa: la comisión varía
  // por medio de pago y por plazo de acreditación—. Un porcentaje hardcodeado
  // daría la misma comisión para los dos y ninguno cuadraría con el extracto.
  const r = resumir({ pagos: [pago({ id: 1, bruto: 360, neto: 330 }),
                              pago({ id: 2, bruto: 360, neto: 300 })] });
  assert.strictEqual(r.dinero.bruto, 720);
  assert.strictEqual(r.dinero.neto_recibido, 630);
  assert.strictEqual(r.dinero.comision_mercadopago, 90);
});

test('un pago sin neto informado se declara, no se estima', () => {
  const r = resumir({ pagos: [pago({ id: 1, bruto: 360, neto: 330 }),
                              pago({ id: 2, bruto: 360, neto: null })] });
  assert.strictEqual(r.dinero.pagos_sin_neto_informado, 1);
  assert.match(r.dinero.nota, /no se estimó/);
  // El bruto sí se cuenta entero: el pago existe.
  assert.strictEqual(r.dinero.bruto, 720);
});

test('sin pagos no inventa moneda', () => {
  assert.strictEqual(resumir({}).dinero.moneda, null);
});

console.log('\nmetricas — los clientes');

test('cuenta personas distintas, no transacciones', () => {
  // El mismo cliente renovando no son dos clientes.
  const r = resumir({ pagos: [pago({ id: 1, email: 'ana@x.com' }),
                              pago({ id: 2, email: 'ANA@x.com' }),
                              pago({ id: 3, email: 'luis@x.com' })] });
  assert.strictEqual(r.clientes.distintos, 2, 'no normalizó mayúsculas');
  assert.strictEqual(r.pagos.aprobados, 3);
});

test('separa por plan y por mes', () => {
  const r = resumir({ pagos: [
    pago({ id: 1, plan: 'professional', fecha: '2026-07-02T10:00:00Z' }),
    pago({ id: 2, plan: 'professional_anual', fecha: '2026-08-02T10:00:00Z', bruto: 3600 }),
  ] });
  assert.deepStrictEqual(Object.keys(r.pagos.por_mes).sort(), ['2026-07', '2026-08']);
  assert.strictEqual(r.pagos.por_plan.professional_anual.bruto, 3600);
});

console.log('\nmetricas — la alerta que importa');

test('un pago aprobado sin licencia emitida aparece como alerta', () => {
  // El escenario exacto de hoy: MercadoPago cobró y la emisión falló porque
  // faltaba la clave privada. Sin esta alerta, el tablero mostraría "1 pago,
  // $360" y todo se vería bien mientras un cliente espera su licencia.
  const r = resumir({ pagos: [pago({ id: 777 })], canjes: [] });
  assert.strictEqual(r.alertas.pagos_sin_licencia, 1);
  assert.strictEqual(r.alertas.detalle[0].payment_id, '777');
});

test('con la licencia emitida, no hay alerta', () => {
  const r = resumir({ pagos: [pago({ id: 777 })],
                      canjes: [{ payment_id: '777', plan: 'professional' }] });
  assert.strictEqual(r.alertas.pagos_sin_licencia, 0);
});

test('el id se compara como texto: 777 numérico y "777" son el mismo pago', () => {
  // MercadoPago devuelve el id como número y el nombre del blob es texto. Si
  // se compararan sin normalizar, TODOS los pagos saldrían como sin licencia.
  const r = resumir({ pagos: [pago({ id: 777 })], canjes: [{ payment_id: 777 }] });
  assert.strictEqual(r.alertas.pagos_sin_licencia, 0);
});

console.log('\nmetricas — las descargas y los huecos');

test('las descargas se reportan tal cual', () => {
  assert.strictEqual(resumir({ descargas: 42 }).descargas.instalador, 42);
});

test('mesDe no revienta con una fecha ausente', () => {
  assert.strictEqual(mesDe(undefined), 'sin-fecha');
  assert.strictEqual(mesDe('2026-08-15T00:00:00Z'), '2026-08');
});

console.log('\nmetricas — la paginación de MercadoPago');

(async () => {
  await testAsync('trae todas las páginas, no sólo la primera', async () => {
    // 50 por página: con un solo pedido, el día que haya 51 ventas el tablero
    // mostraría 50 para siempre y nadie lo notaría.
    const total = 120;
    const falso = async (url) => {
      const offset = Number(new URL(url).searchParams.get('offset'));
      const results = [];
      for (let i = offset; i < Math.min(offset + 50, total); i++) {
        results.push(pago({ id: i, email: `c${i}@x.com` }));
      }
      return { ok: true, json: async () => ({ results }) };
    };
    const pagos = await pagosAprobados('tok', { buscar: falso });
    assert.strictEqual(pagos.length, total);
  });

  await testAsync('un error de MercadoPago no se disfraza de cero ventas', async () => {
    const falso = async () => ({ ok: false, status: 401, json: async () => ({}) });
    await assert.rejects(() => pagosAprobados('tok', { buscar: falso }), /401/);
  });

  if (!process.exitCode) console.log(`\ntodos los tests de métricas pasaron (${pasaron})`);
})();
