// © 2026 Martín Viera. Todos los derechos reservados.
//
// MV Project Management · arranque del servidor local, separado de `main.js`
// a propósito para poder testearlo con Node puro. `main.js` importa esto.
//
// Qué levanta: `api/main.py` (FastAPI), que además sirve la interfaz React en
// `/app`. NO Streamlit. Son dos formas de ver EL MISMO motor:
//
//   .exe instalado  -> React sobre la API      (esta ruta)
//   .bat portable   -> Streamlit               (sin cambios)
//
// El motor de dominio (`mvpm/`) es el mismo en las dos. Si alguna vez
// divergieran, sería el mismo error que ya cometió este producto con las
// listas de firmas revocadas: dos fuentes de verdad que nadie sincroniza.

const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const http = require('node:http');
const net = require('node:net');
const path = require('node:path');

/** Un puerto libre que el sistema operativo elige. */
function puertoLibre() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.listen(0, '127.0.0.1', () => {
      const puerto = srv.address().port;
      srv.close(() => resolve(puerto));
    });
    srv.on('error', reject);
  });
}

/**
 * Intérpretes a probar, EN ORDEN de preferencia:
 *   1. el Python EMBEBIDO que viaja dentro del instalador (`server/python`).
 *      Es el que hace que el `.exe` ande en una PC recién formateada.
 *   2. el `.venv` del repositorio (modo desarrollo).
 *   3. el Python del sistema, como último recurso.
 *
 * El embebido va primero a propósito: si el cliente TIENE Python instalado
 * pero sin fastapi, elegir el suyo haría fallar el arranque teniendo al lado
 * uno que funciona.
 */
function candidatosPython(raiz) {
  const win = process.platform === 'win32';
  const nombres = win ? ['python.exe', 'python3.exe', 'py.exe'] : ['python3', 'python'];
  const propios = win
    ? [path.join(raiz, 'python', 'python.exe'),
       path.join(raiz, '.venv', 'Scripts', 'python.exe')]
    : [path.join(raiz, 'python', 'bin', 'python3'),
       path.join(raiz, '.venv', 'bin', 'python')];
  return [...propios.filter((p) => fs.existsSync(p)), ...nombres];
}

/**
 * ¿Este intérprete sirve? Se pide fastapi + uvicorn y NO streamlit: la versión
 * de escritorio sirve la UI React desde `api/main.py`, y exigir streamlit acá
 * haría fallar el arranque en un empaquetado que —correctamente— no lo lleva.
 */
function pythonSirve(bin, cwd) {
  try {
    const r = spawnSync(bin, ['-c', 'import fastapi, uvicorn, mvpm'],
                        { cwd, timeout: 30000 });
    return r.status === 0;
  } catch {
    return false;
  }
}

/** El primero de la lista que realmente funcione, o null. */
function elegirPython(raiz) {
  for (const bin of candidatosPython(raiz)) {
    if (pythonSirve(bin, raiz)) return bin;
  }
  return null;
}

/**
 * Dónde vive el servidor: la copia empaquetada dentro del instalador, o el
 * repositorio en desarrollo.
 */
function raizServidor(resourcesPath, raizRepo) {
  const instalado = resourcesPath ? path.join(resourcesPath, 'server') : null;
  if (instalado && fs.existsSync(path.join(instalado, 'api', 'main.py'))) {
    return instalado;
  }
  return raizRepo;
}

/**
 * Levanta la API, que además sirve la UI en `/app`.
 *
 * `MVPM_UI_DIR` se pasa explícito porque en el empaquetado de electron-builder
 * la carpeta del bundle NO queda al lado de `api/`: la heurística relativa de
 * `api/main.py` sirve para el repositorio pero no para el `.exe` instalado, y
 * el síntoma sería una ventana en blanco con un 404 en `/app` recién después
 * de instalar, que es el peor momento para descubrirlo.
 */
function lanzarApi(bin, raiz, puerto, dirUi, entornoExtra = {}) {
  return spawn(bin, ['-m', 'uvicorn', 'api.main:app',
                     '--host', '127.0.0.1', '--port', String(puerto)], {
    cwd: raiz,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
      PYTHONPATH: raiz,
      ...(dirUi ? { MVPM_UI_DIR: dirUi } : {}),
      ...entornoExtra,
    },
  });
}

/**
 * Espera a que el servidor conteste. Se consulta `/health`, que NO pasa por el
 * candado de licencia: preguntar por un endpoint con `requiere_acceso` daría
 * 402 en una instalación con la prueba vencida, el lanzador lo leería como
 * "todavía no levantó" y se quedaría esperando hasta el timeout — con el
 * servidor perfectamente vivo del otro lado.
 */
function esperarServidor(puerto, timeoutMs = 180000, pollMs = 700) {
  const url = `http://127.0.0.1:${puerto}/health`;
  const desde = Date.now();
  return new Promise((resolve) => {
    const tick = () => {
      if (Date.now() - desde > timeoutMs) return resolve(false);
      const req = http.get(url, (res) => {
        res.resume();
        if (res.statusCode && res.statusCode < 500) return resolve(true);
        setTimeout(tick, pollMs);
      });
      req.on('error', () => setTimeout(tick, pollMs));
      req.setTimeout(3000, () => { req.destroy(); setTimeout(tick, pollMs); });
    };
    tick();
  });
}

/**
 * Mata el servidor. En Windows se usa `taskkill /T` porque `proc.kill()` mata
 * al padre y deja al Python huérfano ocupando el puerto: al reabrir el
 * programa, el puerto anterior sigue tomado y queda un proceso invisible
 * comiendo memoria hasta que alguien reinicia la máquina.
 */
function detener(proc) {
  if (!proc) return;
  try {
    if (process.platform === 'win32') {
      spawnSync('taskkill', ['/pid', String(proc.pid), '/T', '/F']);
    } else {
      proc.kill('SIGTERM');
    }
  } catch { /* ya estaba muerto */ }
}

/**
 * El motor EMPAQUETADO: el `.exe` que produce PyInstaller.
 *
 * Es la ruta que corre en la PC de un cliente. Se lanza el mismo binario de
 * siempre con `MVPM_MODO=api`, que hace que sirva la interfaz React en vez de
 * Streamlit (`packaging/mvpm_launcher.py`).
 *
 * Por qué no se levanta uvicorn contra el código fuente, como en desarrollo:
 * ese `.exe` es el resultado de compilar `mvpm/` a `.pyd`
 * (`packaging/setup_cython.py` + `strip_py_sources.py`). Correr la API desde
 * afuera obligaría a meter `mvpm/` como `.py` legible dentro del instalador —
 * o sea, regalar el motor en cada descarga. El binario ya sabe hacerlo; sólo
 * hay que pedírselo.
 */
function lanzarMotorEmpaquetado(exe, puerto, dirUi, entornoExtra = {}) {
  return spawn(exe, [], {
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
      MVPM_MODO: 'api',
      MVPM_ELECTRON: '1',       // no abrir además una pestaña del navegador
      MVPM_PORT: String(puerto),
      ...(dirUi ? { MVPM_UI_DIR: dirUi } : {}),
      ...entornoExtra,
    },
  });
}

/**
 * El puerto que el motor ANUNCIA por stdout (`MVPM_READY_PORT:<n>`).
 *
 * No alcanza con el que le pasamos por `MVPM_PORT`. `mvpm/puertos.py` lo
 * respeta sólo SI SIGUE LIBRE, y si no elige otro en vez de morir — que es el
 * comportamiento correcto. Pero entre que Electron encuentra un puerto libre y
 * que el motor lo toma pasa casi un segundo, y en ese hueco cualquier otro
 * proceso puede quedarse con él. Ahí el motor arranca en otro puerto, la
 * ventana apunta al que pidió, y el programa abre en blanco sin ningún error:
 * el servidor está vivo, sólo que en otra puerta.
 *
 * Por eso se escucha lo que el motor dice que hizo, en vez de asumir que hizo
 * lo que se le pidió. Si no lo anuncia antes del timeout, se cae al pedido —
 * que es lo mejor disponible y funciona en el caso normal.
 */
function puertoAnunciado(proc, pedido, timeoutMs = 60000) {
  return new Promise((resolve) => {
    let buffer = '';
    let listo = false;
    const terminar = (puerto) => {
      if (listo) return;
      listo = true;
      clearTimeout(reloj);
      resolve(puerto);
    };
    const reloj = setTimeout(() => terminar(pedido), timeoutMs);
    if (!proc.stdout) return terminar(pedido);
    proc.stdout.on('data', (d) => {
      buffer += d.toString();
      const m = buffer.match(/MVPM_READY_PORT:(\d+)/);
      if (m) terminar(Number(m[1]));
    });
    proc.on('exit', () => terminar(pedido));
  });
}

/** La ruta del `.exe` empaquetado, o null si no está (modo desarrollo). */
function motorEmpaquetado(resourcesPath) {
  if (!resourcesPath) return null;
  const exe = path.join(resourcesPath, 'motor',
    process.platform === 'win32' ? 'MVProjectManagement.exe' : 'MVProjectManagement');
  return fs.existsSync(exe) ? exe : null;
}

module.exports = {
  puertoLibre, candidatosPython, pythonSirve, elegirPython,
  raizServidor, lanzarApi, lanzarMotorEmpaquetado, motorEmpaquetado,
  puertoAnunciado,
  esperarServidor, detener,
};
