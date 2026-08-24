// © 2026 Martín Viera. Todos los derechos reservados.
// Checkout de MercadoPago — función serverless (Vercel, CommonJS).
//
// Dos modalidades de cobro:
//   - "professional"       → SUSCRIPCIÓN mensual recurrente (/preapproval_plan).
//                            MercadoPago cobra solo todos los meses.
//   - "professional_anual" → pago único por 12 meses (/checkout/preferences).
//
// Por qué importa: con /checkout/preferences a secas el cobro es UNA sola vez.
// El cliente pagaba, a los 30 días se le vencía la licencia y tenía que
// acordarse de comprar de nuevo a mano — o sea, no había ingreso recurrente.
// La suscripción lo cobra automáticamente; el pago anual lo evita de raíz.
//
// El Access Token de MercadoPago vive SOLO como variable de entorno del
// servidor (MP_ACCESS_TOKEN). Nunca se expone al navegador ni se guarda en el
// repo. Alternativa sin token: un link de pago fijo por plan (MP_LINK_<PLAN>).
//
// POST + JSON (no GET/redirect): el cliente hace fetch acá, recibe la URL de
// pago y recién después navega él mismo. Así una futura verificación anti-bot
// (Vercel BotID) puede adjuntarse al fetch, que nunca se puede hacer sobre una
// navegación de página completa.

// Protección anti-bot opcional: si el proyecto tiene Vercel BotID configurado
// (paquete `botid`), se usa; si no está instalado/configurado, el checkout
// sigue funcionando igual (no se rompe la venta por falta de hardening).
let checkBotId = null;
try { ({ checkBotId } = require("botid/server")); } catch (_) { /* opcional */ }

// El catálogo de planes, la moneda y la tasa viven en ./_planes.js, compartido
// con verify-payment.js: quien COBRA y quien EMITE la licencia tienen que
// estar mirando exactamente los mismos precios, o se abre un hueco entre los
// dos (pagar un plan y reclamar otro).
const { CURRENCY, TASA_UYU, PLANS } = require("./_planes");

const { limitar } = require("./_ratelimit");
const { registrarUnaVez, porMail, huella } = require("./_aviso");

module.exports = async (req, res) => {
  if (req.method !== "POST") { res.status(405).json({ error: "method" }); return; }

  // Complementa a BotID (que es opcional y puede no estar configurado): crear
  // preferencias de pago contra MercadoPago en bucle es caro y ensucia la
  // cuenta. 10/min por IP no molesta a nadie que esté comprando de verdad.
  if (limitar(req, res, "checkout", { max: 10, ventanaMs: 60_000 })) return;

  if (checkBotId) {
    try {
      const verification = await checkBotId({ advancedOptions: { headers: req.headers } });
      if (verification.isBot) { res.status(403).json({ error: "bot" }); return; }
    } catch (_) { /* si BotID no está configurado, no bloquea la venta */ }
  }

  const body = typeof req.body === "string" ? safeJson(req.body) : (req.body || {});
  const plan = String(body.plan || "").toLowerCase();
  const p = PLANS[plan];
  if (!p) { res.status(400).json({ error: "plan_invalido" }); return; }

  // Aviso de INTENCIÓN de compra: alguien apretó "Comprar".
  //
  // Va acá, antes de hablar con MercadoPago, y no en los cuatro caminos de
  // éxito de abajo. Dos motivos:
  //
  //   1. Un solo lugar. Con cuatro `res.status(200)` distintos, poner el aviso
  //      en cada uno es garantía de que alguno quede sin él la próxima vez que
  //      se toque este archivo.
  //   2. Lo que MÁS interesa saber es justamente lo que hoy no se ve. El
  //      tablero (`/api/metricas`) muestra pagos APROBADOS: quien intentó
  //      comprar y no pudo —MercadoPago caído, tarjeta rechazada, se
  //      arrepintió— es invisible. Avisar antes del intento los captura a
  //      todos, y el desenlace se lee después comparando contra los pagos.
  //
  // `void` y sin `await`: el aviso no puede demorar ni romper el checkout. Una
  // venta perdida por un mail que no salió sería absurdo.
  //
  // El mail sale UNA vez por persona, plan y día. Alguien indeciso que aprieta
  // cinco veces generaba cinco mails idénticos, y a la tercera notificación
  // igual uno deja de mirarlas — ahí el aviso deja de servir para lo único que
  // sirve. La clave es la huella (IP hasheada, no la IP) más el plan.
  const intencion = { plan, referer: String(req.headers.referer || "").slice(0, 200) };
  void (async () => {
    const { nuevo } = await registrarUnaVez(
      "intenciones/", `${huella(req)}-${plan}`, intencion);
    if (!nuevo) return;   // ya avisé por esta persona y este plan, hoy
    await porMail({
      asunto: `Alguien apretó Comprar — plan ${plan}`,
      filas: [["Plan", plan], ["Vino de", intencion.referer || "(sin referer)"]],
      extra: '<p>Todavía no pagó: esto es el click, no la venta. '
        + 'El resultado real se ve en <code>/api/metricas</code>.</p>',
    });
  })().catch(() => {});

  const base = "https://" + (req.headers.host || "");
  const token = process.env.MP_ACCESS_TOKEN;
  const link = process.env["MP_LINK_" + plan.toUpperCase()];

  // Sin Access Token: si hay link de pago fijo configurado, se devuelve ese.
  if (!token) {
    if (link) { res.status(200).json({ url: link, modo: "link_fijo" }); return; }
    res.status(503).json({ error: "medio_pago_no_configurado" });
    return;
  }

  const amount = CURRENCY === "UYU" ? Math.round(p.priceUsd * TASA_UYU) : p.priceUsd;

  try {
    if (p.recurring) {
      // --- Suscripción mensual automática -------------------------------
      const r = await fetch("https://api.mercadopago.com/preapproval_plan", {
        method: "POST",
        headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: p.title,
          auto_recurring: {
            frequency: 1,
            frequency_type: "months",
            transaction_amount: amount,
            currency_id: CURRENCY,
          },
          back_url: base + "/?checkout=success&plan=" + plan,
        }),
      });
      const data = await r.json();
      if (r.ok && data.init_point) {
        res.status(200).json({ url: data.init_point, modo: "suscripcion" });
        return;
      }
      // Si la cuenta no tiene suscripciones habilitadas, no se pierde la
      // venta: se cae al cobro único de 12 meses en vez de romper.
      console.error("preapproval_plan rechazado:", JSON.stringify(data).slice(0, 400));
    }

    // --- Pago único (anual, o fallback de la suscripción) ----------------
    const anual = PLANS.professional_anual;
    const item = p.recurring ? anual : p;
    const unitPrice = CURRENCY === "UYU"
      ? Math.round(item.priceUsd * TASA_UYU)
      : item.priceUsd;

    const r2 = await fetch("https://api.mercadopago.com/checkout/preferences", {
      method: "POST",
      headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
      body: JSON.stringify({
        items: [{
          title: item.title,
          quantity: 1,
          unit_price: unitPrice,
          currency_id: CURRENCY,
        }],
        back_urls: {
          success: base + "/?checkout=success&plan=professional_anual",
          pending: base + "/?checkout=pending&plan=professional_anual",
          failure: base + "/?checkout=failure&plan=professional_anual",
        },
        auto_return: "approved",
        metadata: { plan: "professional_anual" },
      }),
    });
    const data2 = await r2.json();
    if (!r2.ok || !data2.init_point) {
      if (link) { res.status(200).json({ url: link, modo: "link_fijo" }); return; }
      res.status(502).json({ error: "mercadopago" });
      return;
    }
    res.status(200).json({ url: data2.init_point, modo: "pago_unico_anual" });
  } catch (e) {
    if (link) { res.status(200).json({ url: link, modo: "link_fijo" }); return; }
    res.status(500).json({ error: "exception" });
  }
};

function safeJson(s) { try { return JSON.parse(s); } catch (e) { return {}; } }
