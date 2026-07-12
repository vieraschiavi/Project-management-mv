// Checkout de MercadoPago — mismo patrón que api/checkout.js de MV Kobra AI:
// crea una preferencia de pago vía la API REST de MercadoPago (sin SDK, con
// fetch nativo de Node) y redirige al init_point. Si no hay MP_ACCESS_TOKEN
// configurada, cae a un link de pago fijo por plan (MP_LINK_<PLAN>) para que
// el checkout nunca rompa por falta de credenciales — solo deja de ser
// dinámico.
//
// Nota: Kobra protege este endpoint con Vercel BotID (paquete `botid/server`).
// Se omite acá para no sumar una dependencia npm al deploy de solo-HTML;
// es el primer hardening a agregar antes de manejar pagos reales.

const { PLANES } = require('./_license');

const PRECIOS_UNIDAD = {
  professional: { unit_price: 9, currency_id: process.env.MVPM_CURRENCY || 'USD', title: 'MV Project Management — Professional (1 usuario/mes)' },
};

module.exports = async (req, res) => {
  const plan = (req.query.plan || req.body?.plan || 'professional').toString();

  if (!PRECIOS_UNIDAD[plan]) {
    res.status(400).json({ error: `Plan '${plan}' no está a la venta por checkout directo. Para Enterprise, escribinos.` });
    return;
  }

  const accessToken = process.env.MP_ACCESS_TOKEN;
  const fallbackLink = process.env[`MP_LINK_${plan.toUpperCase()}`];

  if (!accessToken) {
    if (fallbackLink) {
      res.writeHead(302, { Location: fallbackLink });
      res.end();
      return;
    }
    res.status(503).json({
      error: 'Checkout no configurado todavía. Faltan MP_ACCESS_TOKEN o MP_LINK_' + plan.toUpperCase() + ' en las variables de entorno de Vercel.',
    });
    return;
  }

  const item = PRECIOS_UNIDAD[plan];
  const origin = `https://${req.headers.host}`;

  try {
    const mpRes = await fetch('https://api.mercadopago.com/checkout/preferences', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        items: [{ title: item.title, quantity: 1, unit_price: item.unit_price, currency_id: item.currency_id }],
        back_urls: {
          success: `${origin}/?checkout=success&plan=${plan}`,
          pending: `${origin}/?checkout=pending&plan=${plan}`,
          failure: `${origin}/?checkout=failure&plan=${plan}`,
        },
        auto_return: 'approved',
        metadata: { plan },
      }),
    });

    if (!mpRes.ok) {
      const detail = await mpRes.text();
      res.status(502).json({ error: 'MercadoPago rechazó la preferencia de pago.', detail });
      return;
    }

    const pref = await mpRes.json();
    res.writeHead(302, { Location: pref.init_point });
    res.end();
  } catch (err) {
    if (fallbackLink) {
      res.writeHead(302, { Location: fallbackLink });
      res.end();
      return;
    }
    res.status(500).json({ error: 'No se pudo iniciar el checkout.', detail: String(err) });
  }
};
