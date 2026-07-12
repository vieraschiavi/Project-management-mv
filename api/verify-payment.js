// Verificación de pago — nunca confía en el query string de retorno de
// MercadoPago (`status=approved` en la URL es trivial de falsificar). Vuelve
// a consultar el pago real contra la API de MercadoPago con el access token
// del servidor antes de emitir la licencia. Mismo criterio que
// api/verify-payment.js de MV Kobra AI.

const { issueLicense } = require('./_license');

module.exports = async (req, res) => {
  const paymentId = (req.query.payment_id || req.query.collection_id || '').toString();
  const plan = (req.query.plan || 'professional').toString();
  const email = (req.query.email || 'cliente@sin-email.local').toString();

  if (!paymentId) {
    res.status(400).json({ error: 'Falta payment_id.' });
    return;
  }

  const accessToken = process.env.MP_ACCESS_TOKEN;
  if (!accessToken) {
    res.status(503).json({ error: 'MP_ACCESS_TOKEN no configurada — no se puede verificar el pago.' });
    return;
  }

  try {
    const mpRes = await fetch(`https://api.mercadopago.com/v1/payments/${encodeURIComponent(paymentId)}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!mpRes.ok) {
      res.status(502).json({ error: 'No se pudo consultar el pago en MercadoPago.' });
      return;
    }
    const payment = await mpRes.json();
    if (payment.status !== 'approved') {
      res.status(402).json({ error: `Pago en estado '${payment.status}', todavía no aprobado.` });
      return;
    }

    const licenseEmail = payment.payer?.email || email;
    const token = issueLicense(plan, licenseEmail, String(payment.id));
    res.status(200).json({ ok: true, plan, license_token: token });
  } catch (err) {
    res.status(500).json({ error: 'Error verificando el pago.', detail: String(err) });
  }
};
