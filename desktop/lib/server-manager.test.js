// © 2026 Martín Viera. Todos los derechos reservados.
//
// Arranque del servidor local — la parte del `.exe` que más se rompe y la que
// menos se ve.
//
// Se testea con Node puro, sin el runtime de Electron: bajarlo no es posible
// en todos los entornos de CI, y si estos chequeos dependieran de él quedarían
// sin correr justo donde importan. Por eso `main.js` no tiene lógica: importa
// de `lib/server-manager.js`, que es lo que se ejercita acá.
//
// Los tres fallos que esto cubre, todos silenciosos:
//
//  1. Elegir un Python que existe pero no sirve. En la PC de un cliente que YA
//     tiene Python instalado sin fastapi, elegir el suyo rompe el arranque
//     teniendo al lado el embebido que funciona.
//  2. Esperar al servidor consultando un endpoint con candado: en una
//     instalación con la prueba vencida devuelve 402, el lanzador lo lee como
//     "todavía no levantó" y se queda esperando con el servidor vivo.
//  3. Dejar el Python huérfano al cerrar: el puerto queda tomado y al reabrir
//     el programa no arranca, sin nada que lo explique.

const assert = require('node:assert');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');

const sm = require('./server-manager');

let pasaron = 0;
async function test(nombre, fn) {
  try { await fn(); console.log(`  ok   ${nombre}`); pasaron++; }
  catch (e) { console.error(`  FALLA ${nombre}\n       ${e.message}`); process.exitCode = 1; }
}

(async () => {

  console.log('server-manager — el puerto');

  await test('devuelve un puerto libre y distinto en cada llamada', async () => {
    const a = await sm.puertoLibre();
    const b = await sm.puertoLibre();
    assert.ok(a > 1024 && a < 65536, `puerto raro: ${a}`);
    assert.notStrictEqual(a, b, 'devolvió el mismo puerto dos veces');
  });

  console.log('\nserver-manager — elegir el Python correcto');

  await test('el embebido y el .venv van ANTES que el del sistema', () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sm-'));
    const win = process.platform === 'win32';
    const propio = win ? path.join(tmp, 'python', 'python.exe')
                       : path.join(tmp, 'python', 'bin', 'python3');
    fs.mkdirSync(path.dirname(propio), { recursive: true });
    fs.writeFileSync(propio, '');
    const lista = sm.candidatosPython(tmp);
    assert.strictEqual(lista[0], propio,
      'el Python embebido no quedó primero: en una PC con Python del sistema '
      + 'sin fastapi, el arranque fallaría teniendo al lado uno que funciona');
    fs.rmSync(tmp, { recursive: true, force: true });
  });

  await test('sin intérpretes propios, quedan los del sistema', () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sm-'));
    const lista = sm.candidatosPython(tmp);
    assert.ok(lista.length >= 2, 'no propuso ningún Python del sistema');
    assert.ok(lista.every((p) => !p.includes(tmp)), 'propuso rutas inexistentes');
    fs.rmSync(tmp, { recursive: true, force: true });
  });

  await test('un binario que no existe no se considera válido', () => {
    assert.strictEqual(sm.pythonSirve('/no/existe/python', process.cwd()), false);
  });

  await test('exige fastapi y uvicorn, NO streamlit', () => {
    // La versión de escritorio sirve React desde la API. Pedir streamlit acá
    // haría fallar el arranque en un empaquetado que —correctamente— no lo
    // incluye, y el síntoma sería "no encontré Python" en una PC que sí lo
    // tiene.
    const fuente = fs.readFileSync(path.join(__dirname, 'server-manager.js'), 'utf-8');
    const linea = fuente.split('\n').find((l) => l.includes("'-c', 'import"));
    assert.ok(linea, 'no encontré la comprobación del intérprete');
    assert.ok(linea.includes('fastapi') && linea.includes('uvicorn'),
      `la comprobación no pide fastapi+uvicorn: ${linea.trim()}`);
    assert.ok(!linea.includes('streamlit'),
      'la comprobación pide streamlit, que el .exe no lleva');
  });

  console.log('\nserver-manager — dónde vive el servidor');

  await test('usa la copia empaquetada cuando existe', () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sm-'));
    fs.mkdirSync(path.join(tmp, 'server', 'api'), { recursive: true });
    fs.writeFileSync(path.join(tmp, 'server', 'api', 'main.py'), '');
    assert.strictEqual(sm.raizServidor(tmp, '/repo'), path.join(tmp, 'server'));
    fs.rmSync(tmp, { recursive: true, force: true });
  });

  await test('cae al repositorio en desarrollo', () => {
    assert.strictEqual(sm.raizServidor(null, '/repo'), '/repo');
    const vacio = fs.mkdtempSync(path.join(os.tmpdir(), 'sm-'));
    assert.strictEqual(sm.raizServidor(vacio, '/repo'), '/repo');
    fs.rmSync(vacio, { recursive: true, force: true });
  });

  console.log('\nserver-manager — esperar al servidor');

  await test('consulta /health y no un endpoint con candado', () => {
    // Si esperara en /api/proyectos, una instalación con la prueba vencida
    // devolvería 402 y el lanzador se quedaría esperando hasta el timeout con
    // el servidor perfectamente vivo del otro lado.
    const fuente = fs.readFileSync(path.join(__dirname, 'server-manager.js'), 'utf-8');
    const linea = fuente.split('\n').find((l) => l.includes('const url ='));
    assert.ok(linea.includes('/health'),
      `espera en un endpoint que no es /health: ${linea.trim()}`);
    assert.ok(!linea.includes('/api/'), 'espera en un endpoint con candado');
  });

  await test('detecta un servidor vivo', async () => {
    const srv = http.createServer((req, res) => { res.writeHead(200); res.end('{}'); });
    await new Promise((r) => srv.listen(0, '127.0.0.1', r));
    const puerto = srv.address().port;
    assert.strictEqual(await sm.esperarServidor(puerto, 5000, 100), true);
    srv.close();
  });

  await test('un 402 cuenta como servidor vivo', async () => {
    // El caso exacto: prueba vencida. El servidor está levantado y contesta;
    // que la respuesta sea "pagá" no lo vuelve inalcanzable.
    const srv = http.createServer((req, res) => { res.writeHead(402); res.end('{}'); });
    await new Promise((r) => srv.listen(0, '127.0.0.1', r));
    const puerto = srv.address().port;
    assert.strictEqual(await sm.esperarServidor(puerto, 5000, 100), true);
    srv.close();
  });

  await test('se rinde si nadie contesta, en vez de colgarse', async () => {
    const libre = await sm.puertoLibre();
    const desde = Date.now();
    assert.strictEqual(await sm.esperarServidor(libre, 1200, 100), false);
    assert.ok(Date.now() - desde < 6000, 'tardó mucho más que el timeout pedido');
  });

  console.log('\nserver-manager — apagar');

  await test('detener() no revienta con null ni con un muerto', () => {
    sm.detener(null);
    sm.detener({ pid: 999999999 });
  });

  await test('en Windows mata el ÁRBOL de procesos', () => {
    // `proc.kill()` mata al padre y deja al Python huérfano ocupando el
    // puerto: al reabrir, el programa no arranca y no hay nada visible que lo
    // explique.
    const fuente = fs.readFileSync(path.join(__dirname, 'server-manager.js'), 'utf-8');
    assert.ok(/taskkill[\s\S]{0,120}'\/T'/.test(fuente),
      'en Windows no se mata el árbol: quedaría un Python huérfano');
  });

  console.log('\nserver-manager — el puerto que el motor ANUNCIA');

  const { EventEmitter } = require('node:events');
  const falsoProc = () => {
    const p = new EventEmitter();
    p.stdout = new EventEmitter();
    return p;
  };

  await test('usa el puerto anunciado y no el pedido', async () => {
    // La carrera real: entre que Electron encuentra un puerto libre y que el
    // motor lo toma, otro proceso se lo puede quedar. `mvpm/puertos.py` elige
    // otro —correctamente— y lo anuncia. Si la ventana apuntara al pedido,
    // abriría en blanco con el servidor vivo en otra puerta.
    const proc = falsoProc();
    const promesa = sm.puertoAnunciado(proc, 9999, 3000);
    proc.stdout.emit('data', 'algo de log\nMVPM_READY_PORT:8123\nmás log\n');
    assert.strictEqual(await promesa, 8123);
  });

  await test('el anuncio partido en varios trozos también se arma', async () => {
    // stdout llega en chunks arbitrarios: el número puede quedar cortado al
    // medio. Sin acumular, el caso normal funcionaría y este no, de forma
    // intermitente — el peor tipo de bug.
    const proc = falsoProc();
    const promesa = sm.puertoAnunciado(proc, 9999, 3000);
    proc.stdout.emit('data', 'MVPM_READY_PO');
    proc.stdout.emit('data', 'RT:8456\n');
    assert.strictEqual(await promesa, 8456);
  });

  await test('si el motor no anuncia nada, cae al puerto pedido', async () => {
    const proc = falsoProc();
    assert.strictEqual(await sm.puertoAnunciado(proc, 7777, 250), 7777);
  });

  await test('si el motor muere antes de anunciar, no se cuelga', async () => {
    const proc = falsoProc();
    const promesa = sm.puertoAnunciado(proc, 7777, 30000);
    proc.emit('exit', 1);
    assert.strictEqual(await promesa, 7777);
  });

  if (!process.exitCode) console.log(`\ntodos los tests del lanzador pasaron (${pasaron})`);
})();
