// Verificación de pago — nunca confía en el query string de retorno de
// MercadoPago (`status=approved` en la URL es trivial de falsificar). Vuelve
// a consultar el pago real contra la API de MercadoPago con el access token
// del servidor antes de emitir la licencia. Mismo criterio que
// api/verify-payment.js de MV Kobra AI.

const { issueLicense } = require('./_license');
const { PLANS, montoAlcanza } = require('./_planes');
const { limitar } = require('./_ratelimit');

module.exports = async (req, res) => {
  // Cada llamada golpea la API de MercadoPago con nuestro access token, así
  // que sin límite alguien puede hacernos consumir cuota probando payment_ids
  // en un bucle. 10/min por IP alcanza de sobra para el uso legítimo: se
  // llama una vez al volver del checkout, más algún reintento.
  if (limitar(req, res, 'verify-payment', { max: 10, ventanaMs: 60_000 })) return;

  const paymentId = (req.query.payment_id || req.query.collection_id || '').toString();
  const planPedido = (req.query.plan || 'professional').toString().toLowerCase();
  const email = (req.query.email || 'cliente@sin-email.local').toString();

  if (!paymentId) {
    res.status(400).json({ error: 'Falta payment_id.' });
    return;
  }

  // El plan se valida ACÁ, que es donde se emite la licencia — no alcanza con
  // que checkout.js lo haya validado al generar el link de pago: este endpoint
  // se puede invocar directo. Sin esto, un pago real de US$9 (Professional)
  // más `&plan=enterprise` en la URL emitía una licencia enterprise con cupo
  // de IA ilimitado.
  if (!PLANS[planPedido]) {
    res.status(400).json({ error: 'Plan inválido o no disponible para compra online.' });
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

    // Qué plan se emite: manda lo que registró el SERVIDOR al crear el cobro
    // (metadata.plan), no lo que dice la URL. El query string sólo se usa como
    // respaldo cuando el pago no trae metadata (p. ej. las suscripciones
    // creadas vía /preapproval_plan, que no la llevan).
    const planEnPago = String(payment.metadata?.plan || '').toLowerCase();
    const plan = PLANS[planEnPago] ? planEnPago : planPedido;

    // Segundo cerrojo, independiente del anterior: que lo efectivamente
    // cobrado alcance para el plan que se va a emitir. Sin esto, un pago
    // aprobado de Professional (US$9) podía canjearse por la licencia anual
    // (US$90) con sólo pedirla en la URL.
    const montoPagado = Number(payment.transaction_amount);
    if (!montoAlcanza(plan, montoPagado)) {
      console.error('monto insuficiente para el plan', { plan, montoPagado, paymentId });
      res.status(402).json({
        error: 'El monto del pago no corresponde al plan solicitado. ' +
               'Escribinos a vieraschiavi@gmail.com con el comprobante y lo resolvemos.',
      });
      return;
    }

    const licenseEmail = payment.payer?.email || email;
    const token = issueLicense(plan, licenseEmail, String(payment.id));
    res.status(200).json({ ok: true, plan, license_token: token });
  } catch (err) {
    res.status(500).json({ error: 'Error verificando el pago.', detail: String(err) });
  }
};
