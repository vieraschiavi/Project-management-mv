// © 2026 Martín Viera. Todos los derechos reservados.
//
// El tablero del dueño: cuántos clientes, cuántas descargas, cuánta plata.
//
// De dónde sale cada número, porque importa más que el número:
//
// * **Dinero** — de la API de MercadoPago (`/v1/payments/search`, sólo
//   `status=approved`). El neto NO se estima: MercadoPago devuelve
//   `transaction_details.net_received_amount`, que es lo que efectivamente
//   entra a la cuenta ya descontada su comisión. Inventar un porcentaje de
//   comisión daría un número que se ve igual de bien y no cuadra con el
//   extracto.
// * **Clientes con licencia** — del registro de canjes en Vercel Blob
//   (`licencias/canjeadas/`), que ya existe para que un pago no se canjee dos
//   veces. Un pago aprobado que no tenga canje es un cliente que pagó y NO
//   tiene su licencia: eso se cuenta aparte y con nombre propio, porque es la
//   única cifra de este tablero que hay que mirar el mismo día.
// * **Descargas** — de `descargas/` en Blob, un objeto por click en el botón
//   de la landing.
//
// Todo lo que falte se informa como faltante. Un tablero que rellena huecos
// con ceros hace creer que no pasó nada cuando lo que pasa es que no se está
// midiendo.

const MP_API = 'https://api.mercadopago.com';

/** Suma los pagos aprobados de MercadoPago, paginando hasta agotar. */
async function pagosAprobados(accessToken, { limite = 1000, buscar = fetch } = {}) {
  const pagos = [];
  let offset = 0;
  while (pagos.length < limite) {
    const url = `${MP_API}/v1/payments/search?status=approved&sort=date_created`
      + `&criteria=desc&limit=50&offset=${offset}`;
    const r = await buscar(url, { headers: { Authorization: `Bearer ${accessToken}` } });
    if (!r.ok) throw new Error(`MercadoPago respondió ${r.status}`);
    const datos = await r.json();
    const lote = datos.results || [];
    pagos.push(...lote);
    // `paging.total` puede mentir por unos pocos registros; el corte real es
    // que un lote venga incompleto.
    if (lote.length < 50) break;
    offset += 50;
  }
  return pagos.slice(0, limite);
}

function mesDe(iso) {
  return typeof iso === 'string' && iso.length >= 7 ? iso.slice(0, 7) : 'sin-fecha';
}

/** El neto real del pago. null si MercadoPago no lo informó todavía. */
function netoDe(pago) {
  const n = pago && pago.transaction_details
    && pago.transaction_details.net_received_amount;
  return typeof n === 'number' ? n : null;
}

function bruto(pago) {
  const n = pago && pago.transaction_amount;
  return typeof n === 'number' ? n : 0;
}

/**
 * Arma el resumen. `pagos` y `canjes` se pasan ya obtenidos para que esto sea
 * pura aritmética y se pueda testear sin red.
 */
function resumir({ pagos = [], canjes = [], descargas = 0 } = {}) {
  const canjeados = new Set(canjes.map((c) => String(c.payment_id)));

  const porMes = {};
  const porPlan = {};
  const emails = new Set();
  let brutoTotal = 0;
  let netoTotal = 0;
  let sinNeto = 0;
  const pagosSinLicencia = [];

  for (const p of pagos) {
    const mes = mesDe(p.date_approved || p.date_created);
    const plan = (p.metadata && p.metadata.plan) || 'desconocido';
    const b = bruto(p);
    const n = netoDe(p);
    if (n === null) sinNeto++;

    brutoTotal += b;
    netoTotal += n === null ? 0 : n;

    porMes[mes] = porMes[mes] || { pagos: 0, bruto: 0, neto: 0 };
    porMes[mes].pagos++;
    porMes[mes].bruto += b;
    porMes[mes].neto += n === null ? 0 : n;

    porPlan[plan] = porPlan[plan] || { pagos: 0, bruto: 0 };
    porPlan[plan].pagos++;
    porPlan[plan].bruto += b;

    const email = (p.payer && p.payer.email) || null;
    if (email) emails.add(email.toLowerCase());

    if (!canjeados.has(String(p.id))) {
      // Pagó y no tiene licencia. Es lo único de este tablero que se mira hoy.
      pagosSinLicencia.push({
        payment_id: String(p.id), fecha: p.date_approved || p.date_created,
        plan, monto: b,
      });
    }
  }

  const redondear = (x) => Math.round(x * 100) / 100;

  return {
    clientes: {
      // Emails distintos que pagaron. Es el número de personas; `pagos` es el
      // de transacciones, y no son lo mismo en cuanto alguien renueva.
      distintos: emails.size,
      licencias_emitidas: canjes.length,
    },
    dinero: {
      moneda: (pagos[0] && pagos[0].currency_id) || null,
      bruto: redondear(brutoTotal),
      neto_recibido: redondear(netoTotal),
      comision_mercadopago: redondear(brutoTotal - netoTotal),
      pagos_sin_neto_informado: sinNeto,
      nota: sinNeto
        ? `${sinNeto} pago(s) todavía sin neto informado por MercadoPago: `
          + 'no se estimó su comisión, se cuentan con neto 0.'
        : null,
    },
    pagos: { aprobados: pagos.length, por_mes: porMes, por_plan: porPlan },
    descargas: { instalador: descargas },
    // Lo que hay que arreglar hoy, si hay algo.
    alertas: {
      pagos_sin_licencia: pagosSinLicencia.length,
      detalle: pagosSinLicencia.slice(0, 20),
    },
  };
}

module.exports = { pagosAprobados, resumir, netoDe, mesDe };
