// Checkout de MercadoPago — función serverless (Vercel, CommonJS).
// Misma estructura que api/checkout.js de MV Kobra AI, con los precios de
// MV Project Management.
//
// El Access Token de MercadoPago vive SOLO como variable de entorno del
// servidor (MP_ACCESS_TOKEN). Nunca se expone al navegador ni se guarda en el
// repo. Alternativa sin token: configurar un link de pago por plan
// (MP_LINK_PROFESSIONAL).
//
// POST + JSON (no GET/redirect): el cliente hace fetch acá, recibe la URL de
// pago y recién después navega él mismo. Mismo patrón que Kobra — así una
// futura verificación anti-bot (Vercel BotID) puede adjuntarse al fetch, que
// nunca se puede hacer sobre una navegación de página completa.

// Protección anti-bot opcional: si el proyecto tiene Vercel BotID configurado
// (paquete `botid`), se usa; si no está instalado/configurado, el checkout
// sigue funcionando igual (no se rompe la venta por falta de hardening).
let checkBotId = null;
try { ({ checkBotId } = require("botid/server")); } catch (_) { /* opcional */ }

const PLANS = {
  professional: { title: "MV Project Management · Professional (mensual, por usuario)", price: 9.0 },
};

// La cuenta de cobro (collector) de MercadoPago es de Uruguay (site MLU), que
// SOLO acepta preferencias en UYU: mandar "USD" hace que la API rechace la
// preferencia (no llega init_point) y el checkout falla. Los precios se
// muestran de referencia en USD pero se cobran en pesos uruguayos al tipo de
// cambio del día — por eso acá se convierte antes de crear la preferencia.
const CURRENCY = process.env.MP_CURRENCY || "UYU";
const TASA_UYU = Number(process.env.MP_TASA_UYU) || 40; // US$1 ≈ $U 40 (referencia)

module.exports = async (req, res) => {
  if (req.method !== "POST") { res.status(405).json({ error: "method" }); return; }

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

  const base = "https://" + (req.headers.host || "");
  const token = process.env.MP_ACCESS_TOKEN;
  const link = process.env["MP_LINK_" + plan.toUpperCase()];

  // Sin Access Token: si hay link de pago fijo configurado, se devuelve ese.
  if (!token) {
    if (link) { res.status(200).json({ url: link }); return; }
    res.status(503).json({ error: "medio_pago_no_configurado" });
    return;
  }

  try {
    const unitPrice = CURRENCY === "UYU" ? Math.round(p.price * TASA_UYU) : p.price;
    const pref = {
      items: [{ title: p.title, quantity: 1, unit_price: unitPrice, currency_id: CURRENCY }],
      back_urls: {
        success: base + "/?checkout=success&plan=" + plan,
        pending: base + "/?checkout=pending&plan=" + plan,
        failure: base + "/?checkout=failure&plan=" + plan,
      },
      auto_return: "approved",
      metadata: { plan: plan },
    };
    const r = await fetch("https://api.mercadopago.com/checkout/preferences", {
      method: "POST",
      headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
      body: JSON.stringify(pref),
    });
    const data = await r.json();
    if (!r.ok || !data.init_point) {
      res.status(502).json({ error: "mercadopago" });
      return;
    }
    res.status(200).json({ url: data.init_point });
  } catch (e) {
    if (link) { res.status(200).json({ url: link }); return; }
    res.status(500).json({ error: "exception" });
  }
};

function safeJson(s) { try { return JSON.parse(s); } catch (e) { return {}; } }
