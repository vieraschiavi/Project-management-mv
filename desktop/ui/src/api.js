// © 2026 Martín Viera. Todos los derechos reservados.
/*
 * Cliente de la API del motor (api/main.py).
 *
 * La UI se sirve DESDE el mismo servidor (FastAPI la monta en /app), así que
 * las llamadas son de mismo origen: sin CORS, sin file://, sin puerto
 * hardcodeado. `location.origin` da el 127.0.0.1:<puerto> real, sea cual sea
 * el puerto libre que eligió el lanzador.
 */

const BASE = (typeof window !== 'undefined' && window.MVPM_API_BASE) || '';

export class ApiError extends Error {
  constructor(clase, detalle, status) {
    super(clase);
    this.clase = clase;
    this.detalle = detalle || '';
    this.status = status || 0;
  }
}

async function pedir(ruta, opciones = {}) {
  let r;
  try {
    r = await fetch(`${BASE}${ruta}`, opciones);
  } catch (e) {
    // fetch sólo rechaza por red: el servidor todavía no levantó, o murió.
    throw new ApiError('sin_conexion', `${ruta} · ${e.message}`, 0);
  }
  if (!r.ok) {
    let detalle = `HTTP ${r.status}`;
    try {
      const cuerpo = await r.json();
      if (cuerpo && cuerpo.detail) detalle = cuerpo.detail;
    } catch { /* el cuerpo puede no ser JSON; el status ya dice bastante */ }
    // 402 es "la prueba venció o falta licencia" y NO es un error técnico: la
    // interfaz lo trata como un estado del programa, con su propia pantalla.
    throw new ApiError(r.status === 402 ? 'sin_licencia' : 'respuesta_invalida',
                       detalle, r.status);
  }
  return r.json();
}

/** Estado del candado. Lo PRIMERO que se consulta al abrir. */
export const acceso = () => pedir('/licencias/acceso');

export const activar = (token) => pedir('/licencias/activar', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ token }),
});

export const desactivar = () => pedir('/licencias/activar', { method: 'DELETE' });

export const planes = () => pedir('/licencias/planes');

const tabla = (nombre) => pedir(`/api/${nombre}`);

/**
 * Todo el portafolio de una vez.
 *
 * `Promise.all` y no una cadena de `await`: son seis pedidos independientes al
 * mismo servidor local. En serie, el arranque tarda la suma; en paralelo, lo
 * que tarde el más lento. Sobre localhost la diferencia se nota igual porque
 * cada uno recalcula las tablas del motor.
 */
export async function portafolio() {
  const [proyectos, tareas, equipo, salud, politicas, backlog] = await Promise.all([
    tabla('proyectos'), tabla('tareas'), tabla('equipo'),
    tabla('salud'), tabla('politicas'), tabla('backlog_priorizado'),
  ]);
  return { proyectos, tareas, equipo, salud, politicas, backlog };
}
