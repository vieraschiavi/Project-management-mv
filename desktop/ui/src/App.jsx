// © 2026 Martín Viera. Todos los derechos reservados.
/*
 * MV Project Management · interfaz de escritorio (React).
 *
 * Reemplaza a Streamlit en la versión `.exe`: consume la API REST del motor
 * (`api/main.py`) y dibuja el portafolio con componentes propios. El `.bat`
 * portable sigue usando Streamlit — son dos formas de ver EL MISMO motor, no
 * dos productos. Ninguna de las dos calcula nada: la salud, el índice y el
 * valor esperado llegan ya resueltos del motor, y esta capa sólo los muestra.
 *
 * Por qué no hay librería de gráficos: las dos vistas que la pedirían (salud
 * por dimensión y por proyecto) son barras horizontales de 0 a 100. Un <div>
 * con un ancho porcentual las resuelve y evita sumarle cientos de KB al bundle
 * — y, sobre todo, evita una dependencia más que auditar en un programa que se
 * vende y promete funcionar sin internet.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ApiError, acceso, activar, desactivar, portafolio } from './api';
import { t } from './i18n';

const VISTAS = ['panorama', 'proyectos', 'salud', 'tareas', 'backlog',
                'equipo', 'politicas', 'licencia'];

const DIMENSIONES = ['alcance', 'cronograma', 'presupuesto', 'riesgo',
                     'dependencias', 'equipo'];

/* --------------------------------------------------------------- helpers */

const num = (v, dec = 0) => (
  v === null || v === undefined || v === '' || Number.isNaN(Number(v))
    ? '—'
    : Number(v).toLocaleString(undefined,
        { minimumFractionDigits: dec, maximumFractionDigits: dec }));

const moneda = (v) => (
  v === null || v === undefined || Number.isNaN(Number(v))
    ? '—'
    : Number(v).toLocaleString(undefined,
        { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }));

/**
 * El color del semáforo.
 *
 * Cuando la fila TRAE `estado`, se usa ese y no se vuelve a calcular nada: el
 * motor ya decidió (`mvpm/health.py`), y recalcularlo acá sería tener el
 * umbral escrito dos veces en dos lenguajes. Escribí esta función con
 * umbrales inventados (70/40) antes de mirar el motor, y estaban mal: los
 * reales son 55 y 75. Ese es exactamente el fallo que este diseño evita.
 *
 * Los umbrales sólo se usan para las barras POR DIMENSIÓN, que son promedios
 * calculados en esta pantalla y no tienen `estado` propio.
 * `tests/test_ui_escritorio.py` los compara contra `mvpm/health.py` para que
 * no se separen en silencio.
 */
const UMBRAL_RIESGO = 55;
const UMBRAL_OBSERVACION = 75;

function color(indice) {
  const v = Number(indice);
  if (Number.isNaN(v)) return 'gris';
  if (v >= UMBRAL_OBSERVACION) return 'verde';
  if (v >= UMBRAL_RIESGO) return 'ambar';
  return 'rojo';
}

/** El color que corresponde a un `estado` del motor. */
const COLOR_ESTADO = { saludable: 'verde', observacion: 'ambar', riesgo: 'rojo' };
const colorDe = (fila) => (
  fila && fila.estado && COLOR_ESTADO[fila.estado]
    ? COLOR_ESTADO[fila.estado]
    : color(fila && fila.indice));

const texto = (fila) => Object.values(fila)
  .map((v) => String(v === null || v === undefined ? '' : v)).join(' ').toLowerCase();

/* ------------------------------------------------------------ componentes */

function Barras({ filas, etiqueta, valor, lang }) {
  if (!filas.length) return <p className="sub">{t('sin_datos', lang)}</p>;
  return (
    <div className="barras">
      {filas.map((f, i) => {
        const v = Number(valor(f)) || 0;
        return (
          <div className="barra" key={i}>
            <div className="barra-n" title={etiqueta(f)}>{etiqueta(f)}</div>
            <div className="pista">
              <div className={`relleno ${colorDe(f) === 'gris' ? color(v) : colorDe(f)}`}
                   style={{ width: `${Math.max(0, Math.min(100, v))}%` }} />
            </div>
            <div className="barra-v">{num(v, 1)}</div>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Tabla con buscador. `columnas` = [{clave, etiqueta, render?, alinear?}].
 *
 * El buscador filtra sobre la fila COMPLETA y no sólo sobre las columnas
 * visibles: buscar el nombre de un responsable tiene que encontrar algo aunque
 * esa columna no se esté mostrando en esta vista.
 */
function Tabla({ filas, columnas, lang }) {
  const [q, setQ] = useState('');
  const filtradas = useMemo(() => {
    const b = q.trim().toLowerCase();
    return b ? filas.filter((f) => texto(f).includes(b)) : filas;
  }, [filas, q]);

  if (!filas.length) return <p className="sub">{t('sin_datos', lang)}</p>;

  return (
    <>
      <div className="tabla-head">
        <input className="buscador" type="search" value={q}
               placeholder={t('buscar', lang)} aria-label={t('buscar', lang)}
               onChange={(e) => setQ(e.target.value)} />
        <span className="sub">{filtradas.length} {t('filas', lang)}</span>
      </div>
      <div className="scroll">
        <table>
          <thead>
            <tr>{columnas.map((c) => (
              <th key={c.clave} className={c.alinear === 'num' ? 'num' : ''}>
                {t(c.etiqueta, lang)}
              </th>))}
            </tr>
          </thead>
          <tbody>
            {filtradas.map((f, i) => (
              <tr key={i}>
                {columnas.map((c) => (
                  <td key={c.clave} className={c.alinear === 'num' ? 'num' : ''}>
                    {c.render ? c.render(f) : (f[c.clave] ?? '—')}
                  </td>))}
              </tr>))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Chip({ estado, lang }) {
  const c = COLOR_ESTADO[estado] || 'gris';
  return <span className={`chip ${c}`}>{t(`estado_${estado}`, lang) || estado}</span>;
}

function Kpi({ etiqueta, valor, sub, lang }) {
  return (
    <div className="kpi">
      <div className="kpi-e">{t(etiqueta, lang)}</div>
      <div className="kpi-v">{valor}</div>
      {sub ? <div className="kpi-s">{sub}</div> : null}
    </div>
  );
}

/* ---------------------------------------------------------------- vistas */

function Panorama({ datos, lang }) {
  const { proyectos, tareas, salud } = datos;
  const indice = salud.length
    ? salud.reduce((a, s) => a + (Number(s.indice) || 0), 0) / salud.length : 0;
  const enRojo = salud.filter((s) => s.estado === 'riesgo').length;
  // 'done' y no 'hecho': los estados del motor son todo/in_progress/blocked/done
  // (mvpm/health.py los usa así). Comparar contra una traducción dejaría el
  // contador midiendo siempre el total.
  const abiertas = tareas.filter((x) => x.estado !== 'done').length;
  const hoy = new Date().toISOString().slice(0, 10);
  const vencidas = tareas.filter((x) => x.vencimiento
    && String(x.vencimiento).slice(0, 10) < hoy && x.estado !== 'done').length;
  const presupuesto = proyectos.reduce((a, p) => a + (Number(p.presupuesto) || 0), 0);
  const ejecutado = proyectos.reduce((a, p) => a + (Number(p.ejecutado) || 0), 0);

  // Promedio por dimensión: el motor ya manda cada dimensión por proyecto, así
  // que acá sólo se promedia. Es la única cuenta de toda la interfaz.
  const porDimension = DIMENSIONES.map((d) => ({
    dim: d,
    valor: salud.length
      ? salud.reduce((a, s) => a + (Number(s[`dim_${d}`]) || 0), 0) / salud.length : 0,
  })).sort((a, b) => a.valor - b.valor);

  return (
    <>
      <div className="kpis">
        <Kpi etiqueta="kpi_proyectos" valor={num(proyectos.length)} lang={lang} />
        <Kpi etiqueta="kpi_salud" valor={num(indice, 1)} lang={lang} />
        <Kpi etiqueta="kpi_riesgo" valor={num(enRojo)} lang={lang} />
        <Kpi etiqueta="kpi_tareas" valor={num(abiertas)} lang={lang} />
        <Kpi etiqueta="kpi_vencidas" valor={num(vencidas)} lang={lang} />
        <Kpi etiqueta="kpi_presupuesto" valor={moneda(ejecutado)}
             sub={`de ${moneda(presupuesto)}`} lang={lang} />
      </div>

      <h2>{t('salud_por_dimension', lang)}</h2>
      <p className="sub">
        {t('peor_dimension', lang)}: <b>{t(`dim_${porDimension[0]?.dim}`, lang)}</b>
      </p>
      <Barras filas={porDimension} lang={lang}
              etiqueta={(f) => t(`dim_${f.dim}`, lang)} valor={(f) => f.valor} />

      <h2>{t('salud_por_proyecto', lang)}</h2>
      <Barras filas={[...salud].sort((a, b) => a.indice - b.indice)} lang={lang}
              etiqueta={(f) => f.nombre} valor={(f) => f.indice} />
    </>
  );
}

function Licencia({ estadoAcceso, onCambio, lang }) {
  const [token, setToken] = useState('');
  const [activando, setActivando] = useState(false);
  const [mensaje, setMensaje] = useState(null);

  const enviar = async (e) => {
    e.preventDefault();
    setActivando(true);
    setMensaje(null);
    try {
      await activar(token.trim());
      setToken('');
      setMensaje({ tipo: 'ok', texto: t('lic_ok', lang) });
      onCambio();
    } catch (err) {
      const clave = err.status === 507 ? 'lic_no_guardada' : 'lic_invalida';
      setMensaje({ tipo: 'error', texto: t(clave, lang) });
    } finally {
      setActivando(false);
    }
  };

  const quitar = async () => {
    await desactivar().catch(() => {});
    onCambio();
  };

  const modo = estadoAcceso?.modo;
  return (
    <div className="panel-lic">
      <h2>{t('lic_titulo', lang)}</h2>

      {modo === 'owner' && <p className="estado verde">{t('lic_owner', lang)}</p>}
      {modo === 'licencia' && (
        <p className="estado verde">
          {t('lic_activa', lang)} — {t('lic_plan', lang)}: <b>{estadoAcceso.plan}</b>
        </p>)}
      {modo === 'trial' && (
        <p className="estado ambar">
          {t('lic_trial', lang)}: {estadoAcceso.dias_restantes} {t('lic_dias', lang)}
        </p>)}
      {modo === 'expirado' && (
        <>
          <p className="estado rojo">{t('lic_vencida', lang)}</p>
          <p className="sub">{t('lic_vencida_texto', lang)}</p>
        </>)}

      {modo !== 'owner' && (
        <form onSubmit={enviar} className="form-lic">
          <input type="password" value={token} autoComplete="off"
                 placeholder={t('lic_pegar', lang)} aria-label={t('lic_pegar', lang)}
                 onChange={(e) => setToken(e.target.value)} required />
          <button type="submit" disabled={activando || !token.trim()}>
            {activando ? t('lic_activando', lang) : t('lic_activar', lang)}
          </button>
        </form>)}

      {mensaje && (
        <p className={`estado ${mensaje.tipo === 'ok' ? 'verde' : 'rojo'}`}>
          {mensaje.texto}
        </p>)}

      {modo === 'licencia' && (
        <button className="link" type="button" onClick={quitar}>
          {t('lic_quitar', lang)}
        </button>)}
    </div>
  );
}

/* ------------------------------------------------------------------- app */

export default function App() {
  const [lang, setLang] = useState('es');
  const [vista, setVista] = useState('panorama');
  const [estadoAcceso, setEstadoAcceso] = useState(null);
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(true);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      // Primero el candado y después los datos: si la prueba venció, pedir el
      // portafolio da 402 y lo único que hay para mostrar es la pantalla de
      // licencia. Al revés se vería un error técnico donde en realidad hay una
      // decisión de negocio esperando.
      const acc = await acceso();
      setEstadoAcceso(acc);
      if (!acc.acceso) {
        setDatos(null);
        setVista('licencia');
        return;
      }
      setDatos(await portafolio());
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError('desconocido', String(e)));
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  if (cargando && !datos) {
    return <div className="centro"><div className="spinner" />{t('cargando', lang)}</div>;
  }

  if (error) {
    return (
      <div className="centro">
        <h2>{t('error_conexion', lang)}</h2>
        <p className="sub">{t('error_detalle', lang)}: {error.detalle}</p>
        <button onClick={cargar}>{t('reintentar', lang)}</button>
      </div>);
  }

  const col = (clave, etiqueta, extra = {}) => ({ clave, etiqueta, ...extra });

  return (
    <div className="app">
      <aside>
        <div className="marca">{t('app', lang)}</div>
        <nav>
          {VISTAS.map((v) => (
            <button key={v} className={v === vista ? 'sel' : ''}
                    onClick={() => setVista(v)}
                    disabled={v !== 'licencia' && !datos}>
              {t(`nav_${v}`, lang)}
            </button>))}
        </nav>
        <div className="pie">
          <select value={lang} onChange={(e) => setLang(e.target.value)}
                  aria-label="Idioma / Language / Idioma">
            <option value="es">Español</option>
            <option value="en">English</option>
            <option value="pt">Português</option>
          </select>
          <button className="link" onClick={cargar}>{t('actualizar', lang)}</button>
        </div>
      </aside>

      <main>
        {vista === 'licencia' ? (
          <Licencia estadoAcceso={estadoAcceso} onCambio={cargar} lang={lang} />
        ) : !datos ? (
          <p className="sub">{t('sin_datos', lang)}</p>
        ) : vista === 'panorama' ? (
          <Panorama datos={datos} lang={lang} />
        ) : vista === 'proyectos' ? (
          <Tabla lang={lang} filas={datos.proyectos} columnas={[
            col('nombre', 'col_nombre'), col('portafolio', 'col_portafolio'),
            col('sponsor', 'col_sponsor'), col('dueno', 'col_dueno'),
            col('criticidad', 'col_criticidad'),
            col('presupuesto', 'col_presupuesto',
                { alinear: 'num', render: (f) => moneda(f.presupuesto) }),
            col('ejecutado', 'col_ejecutado',
                { alinear: 'num', render: (f) => moneda(f.ejecutado) }),
          ]} />
        ) : vista === 'salud' ? (
          <Tabla lang={lang} filas={datos.salud} columnas={[
            col('nombre', 'col_nombre'),
            col('indice', 'col_indice',
                { alinear: 'num', render: (f) => num(f.indice, 1) }),
            col('estado', 'col_estado',
                { render: (f) => <Chip estado={f.estado} lang={lang} /> }),
            ...DIMENSIONES.map((d) => col(`dim_${d}`, `dim_${d}`,
              { alinear: 'num', render: (f) => num(f[`dim_${d}`], 0) })),
          ]} />
        ) : vista === 'tareas' ? (
          <Tabla lang={lang} filas={datos.tareas} columnas={[
            col('titulo', 'col_titulo'), col('proyecto_id', 'col_proyecto'),
            col('responsable', 'col_responsable'), col('estado', 'col_estado'),
            col('vencimiento', 'col_vencimiento'), col('prioridad', 'col_prioridad'),
          ]} />
        ) : vista === 'backlog' ? (
          <Tabla lang={lang} filas={datos.backlog} columnas={[
            col('titulo', 'col_titulo'), col('proyecto_id', 'col_proyecto'),
            col('valor_esperado', 'col_valor',
                { alinear: 'num', render: (f) => num(f.valor_esperado, 1) }),
            col('tareas_impactadas', 'col_impacto', { alinear: 'num' }),
            col('dias_restantes', 'col_dias', { alinear: 'num' }),
            col('responsable', 'col_responsable'),
          ]} />
        ) : vista === 'equipo' ? (
          <Tabla lang={lang} filas={datos.equipo} columnas={[
            col('nombre', 'col_nombre'), col('rol', 'col_rol'),
            col('capacidad_semanal_hs', 'col_capacidad', { alinear: 'num' }),
            col('carga_actual_hs', 'col_carga', { alinear: 'num' }),
          ]} />
        ) : (
          <Tabla lang={lang} filas={datos.politicas} columnas={[
            col('politica', 'col_politica'), col('descripcion', 'col_descripcion'),
            col('estado', 'col_estado'), col('evidencia', 'col_evidencia'),
          ]} />
        )}
      </main>
    </div>
  );
}
