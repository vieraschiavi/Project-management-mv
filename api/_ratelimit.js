// Rate limiting para las funciones serverless públicas.
//
// ALCANCE REAL (importante, para no sobrevender esto): el estado vive en la
// memoria de la instancia, así que el límite es POR INSTANCIA de la función,
// no global. Vercel puede tener varias instancias vivas a la vez y las recicla,
// con lo cual un atacante distribuido puede superar el límite nominal.
//
// Aun así vale la pena: corta en seco el caso realista —alguien golpeando un
// endpoint en un bucle desde una máquina— que sin esto llega directo a la API
// de MercadoPago y puede hacernos consumir cuota o plata. Para un límite duro
// y global hay que respaldarlo con un store compartido (Vercel KV / Upstash);
// queda anotado como el próximo paso si el tráfico lo justifica.

const CUBOS = new Map();

/** Limpia las ventanas vencidas para que el Map no crezca sin techo. */
function purgar(ahora) {
  for (const [k, v] of CUBOS) {
    if (v.reinicia <= ahora) CUBOS.delete(k);
  }
}

/** IP del cliente detrás del proxy de Vercel. */
function ipDe(req) {
  const fwd = req.headers?.['x-forwarded-for'];
  if (typeof fwd === 'string' && fwd.length) return fwd.split(',')[0].trim();
  if (Array.isArray(fwd) && fwd.length) return String(fwd[0]).trim();
  return req.headers?.['x-real-ip'] || req.socket?.remoteAddress || 'desconocida';
}

/**
 * Consume un turno para `clave` (normalmente endpoint + IP).
 * Devuelve {ok, restantes, reintentarEn} sin lanzar.
 */
function consumir(clave, { max = 20, ventanaMs = 60_000 } = {}) {
  const ahora = Date.now();
  if (CUBOS.size > 5000) purgar(ahora);

  const actual = CUBOS.get(clave);
  if (!actual || actual.reinicia <= ahora) {
    CUBOS.set(clave, { usados: 1, reinicia: ahora + ventanaMs });
    return { ok: true, restantes: max - 1, reintentarEn: 0 };
  }
  if (actual.usados >= max) {
    return { ok: false, restantes: 0, reintentarEn: Math.ceil((actual.reinicia - ahora) / 1000) };
  }
  actual.usados += 1;
  return { ok: true, restantes: max - actual.usados, reintentarEn: 0 };
}

/**
 * Aplica el límite y, si se pasó, responde 429 y devuelve true (el handler
 * debe cortar). Si hay lugar, devuelve false y sigue el flujo normal.
 */
function limitar(req, res, nombre, opciones = {}) {
  const r = consumir(`${nombre}:${ipDe(req)}`, opciones);
  if (r.ok) return false;
  res.setHeader?.('Retry-After', String(r.reintentarEn));
  res.status(429).json({
    error: 'Demasiados intentos seguidos. Esperá un momento y probá de nuevo.',
    reintentar_en_segundos: r.reintentarEn,
  });
  return true;
}

module.exports = { limitar, consumir, ipDe };
