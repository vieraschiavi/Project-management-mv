// © 2026 Martín Viera. Todos los derechos reservados.
// Catálogo de planes VENDIBLES online y su precio esperado.
//
// Vive en un módulo aparte a propósito: antes checkout.js sabía qué se puede
// comprar y a qué precio, pero verify-payment.js —que es quien realmente EMITE
// la licencia— no lo sabía, y aceptaba el plan que viniera en el query string.
// Con las dos puntas leyendo de acá, no pueden divergir.
//
// 'enterprise' y 'demo' NO están y no deben estar: enterprise se cotiza por
// proyecto y se entrega a mano desde owner/panel.py; demo no se cobra. Que no
// figuren acá es lo que impide que alguien se auto-emita una licencia
// enterprise (cupo de IA ilimitado) pagando el plan más barato.

// La cuenta de cobro es de Uruguay (site MLU) y sólo acepta UYU: los precios se
// muestran en USD de referencia y se cobran en pesos al cambio del día.
const CURRENCY = process.env.MP_CURRENCY || "UYU";
const TASA_UYU = Number(process.env.MP_TASA_UYU) || 40;

const PLANS = {
  professional: {
    title: "MV Project Management · Professional",
    priceUsd: 9.0,
    recurring: true,          // suscripción mensual automática
  },
  professional_anual: {
    title: "MV Project Management · Professional (12 meses)",
    priceUsd: 90.0,           // 12 meses al precio de 10: 2 meses bonificados
    recurring: false,         // pago único
  },
};

/** Monto que debería haberse cobrado por un plan, en la moneda de cobro. */
function montoEsperado(plan) {
  const p = PLANS[plan];
  if (!p) return null;
  return CURRENCY === "UYU" ? Math.round(p.priceUsd * TASA_UYU) : p.priceUsd;
}

/**
 * ¿El monto realmente cobrado alcanza para el plan que se reclama?
 *
 * Se usa un margen del 15% hacia abajo porque el precio se fija en USD pero se
 * cobra en pesos: entre que se genera el link y que el pago se acredita, el
 * tipo de cambio puede haberse movido. El margen tolera esa deriva sin dejar
 * pasar el salto de un plan a otro, que es de 10x (US$9 vs US$90).
 */
function montoAlcanza(plan, montoPagado) {
  const esperado = montoEsperado(plan);
  if (esperado === null) return false;
  if (!Number.isFinite(montoPagado) || montoPagado <= 0) return false;
  return montoPagado >= esperado * 0.85;
}

module.exports = { CURRENCY, TASA_UYU, PLANS, montoEsperado, montoAlcanza };
