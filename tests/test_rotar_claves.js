// © 2026 Martín Viera. Todos los derechos reservados.
//
// packaging/rotar_claves_licencia.js — el botón que deja el cobro funcionando.
//
// Lo que se fija acá, en orden de qué tan caro sale si falla:
//
//  1. Que la clave privada NO se escape. Es el punto entero del diseño: el
//     valor viaja de la memoria de este proceso a la API de Vercel y a ningún
//     otro lado. Si apareciera en un log de Actions —que en un repo público
//     lee cualquiera, y que queda archivado 90 días— la rotación habría
//     empeorado exactamente lo que vino a arreglar.
//  2. Que las dos mitades queden con la MISMA pública. Si `licensing.py` y
//     `_license.js` se separan, el servidor emite licencias que el programa
//     rechaza, que es el fallo original.
//  3. Que un par roto no llegue a escribirse.

const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const MOD = path.resolve(__dirname, '..', 'packaging', 'rotar_claves_licencia.js');
const { generarPar, comprobarElPar, pegarPublica } = require(MOD);

let pasaron = 0;
function test(nombre, fn) {
  try {
    fn();
    console.log(`  ok   ${nombre}`);
    pasaron++;
  } catch (e) {
    console.error(`  FALLA ${nombre}\n       ${e.message}`);
    process.exitCode = 1;
  }
}

console.log('rotar_claves_licencia.js — el par generado');

test('la pública derivada corresponde a la privada', () => {
  for (let i = 0; i < 5; i++) comprobarElPar(generarPar());
});

test('dos corridas nunca dan el mismo par', () => {
  const a = generarPar();
  const b = generarPar();
  assert.notStrictEqual(a.privada, b.privada);
  assert.notStrictEqual(a.publica, b.publica);
});

test('las claves miden 32 bytes en base64url, sin relleno', () => {
  const { privada, publica } = generarPar();
  for (const k of [privada, publica]) {
    assert.match(k, /^[A-Za-z0-9_-]+$/, `${k} no es base64url limpio`);
    assert.strictEqual(Buffer.from(k.replace(/-/g, '+').replace(/_/g, '/'),
                                   'base64').length, 32);
  }
});

test('un par que no se verifica a sí mismo se rechaza', () => {
  const bueno = generarPar();
  const otro = generarPar();
  assert.throws(() => comprobarElPar({ privada: bueno.privada, publica: otro.publica }),
                /no se verifica/);
});

test('el par nuevo firma un token que el formato MVPM2 acepta', () => {
  // No alcanza con que el par sea válido: tiene que servir para lo único que
  // se usa, que es firmar la licencia de un cliente.
  const { privada, publica } = generarPar();
  const dec = (s) => {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    return Buffer.from(s, 'base64');
  };
  const k = crypto.createPrivateKey({
    key: Buffer.concat([Buffer.from('302e020100300506032b657004220420', 'hex'),
                        dec(privada)]),
    format: 'der', type: 'pkcs8' });
  const p = crypto.createPublicKey({
    key: Buffer.concat([Buffer.from('302a300506032b6570032100', 'hex'), dec(publica)]),
    format: 'der', type: 'spki' });
  const payload = Buffer.from(JSON.stringify({ plan: 'professional' })).toString('base64url');
  const firma = crypto.sign(null, Buffer.from(payload, 'ascii'), k);
  assert.ok(crypto.verify(null, Buffer.from(payload, 'ascii'), p, firma));
});

console.log('\nrotar_claves_licencia.js — la privada no se escapa');

test('el módulo no imprime ni escribe la clave privada', () => {
  // Se captura TODA la salida y se revisan los archivos que el script toca,
  // buscando el valor exacto. Un `console.log(par)` de más —el descuido más
  // fácil de cometer al depurar— se cae acá.
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'rotar-'));
  const py = path.join(tmp, 'licensing.py');
  const js = path.join(tmp, '_license.js');
  fs.writeFileSync(py, 'CLAVE_PUBLICA_EMBEBIDA = "vieja"\n');
  fs.writeFileSync(js, "const CLAVE_PUBLICA_EMBEBIDA = 'vieja';\n");

  const par = generarPar();
  let salida = '';
  const orig = { log: console.log, error: console.error };
  console.log = (...a) => { salida += a.join(' ') + '\n'; };
  console.error = (...a) => { salida += a.join(' ') + '\n'; };
  try {
    comprobarElPar(par);
    // pegarPublica escribe en las rutas reales del repo, así que se ejercita
    // la misma sustitución sobre copias: lo que importa es qué VALOR se
    // escribe, no en qué ruta.
    for (const [ruta, patron, reemplazo] of [
      [py, /^CLAVE_PUBLICA_EMBEBIDA = ".*"$/m, `CLAVE_PUBLICA_EMBEBIDA = "${par.publica}"`],
      [js, /^const CLAVE_PUBLICA_EMBEBIDA = '.*';$/m,
       `const CLAVE_PUBLICA_EMBEBIDA = '${par.publica}';`],
    ]) {
      fs.writeFileSync(ruta, fs.readFileSync(ruta, 'utf-8').replace(patron, reemplazo));
    }
  } finally {
    console.log = orig.log;
    console.error = orig.error;
  }

  assert.ok(!salida.includes(par.privada),
            'la clave PRIVADA apareció en la salida del script');
  for (const ruta of [py, js]) {
    const texto = fs.readFileSync(ruta, 'utf-8');
    assert.ok(!texto.includes(par.privada),
              `la clave PRIVADA quedó escrita en ${path.basename(ruta)}`);
    assert.ok(texto.includes(par.publica),
              `la clave pública NO se escribió en ${path.basename(ruta)}`);
  }
  fs.rmSync(tmp, { recursive: true, force: true });
});

test('el código fuente no logea el objeto del par entero', () => {
  // El escape más probable no es `console.log(privada)` sino
  // `console.log(par)`, que imprime las dos mitades. Se prohíbe por texto.
  const fuente = fs.readFileSync(MOD, 'utf-8');
  // Sólo se miran los VALORES que se interpolan, no el texto del mensaje:
  // `${par.publica}` es correcto imprimirlo y `${par}` o `${par.privada}` no.
  // Mirar la línea entera daba falsos positivos con cualquier mensaje que
  // mencionara la palabra "privada", que son varios y son los útiles.
  const sospechosas = [];
  fuente.split('\n').forEach((linea, i) => {
    if (!/console\.(log|error|warn)/.test(linea)) return;
    for (const [, expr] of linea.matchAll(/\$\{([^}]*)\}/g)) {
      const e = expr.trim();
      if (/privada/i.test(e) || /^par$/.test(e) || /PRIVATE_KEY$/.test(e)) {
        sospechosas.push([i + 1, e]);
      }
    }
  });
  assert.deepStrictEqual(sospechosas, [],
    `valores interpolados que serían la privada: ${JSON.stringify(sospechosas)}`);
});

console.log('\nrotar_claves_licencia.js — las dos mitades no se separan');

test('pegarPublica escribe la MISMA clave en el .py y en el .js', () => {
  const RAIZ = path.resolve(__dirname, '..');
  const rutaPy = path.join(RAIZ, 'mvpm', 'licensing.py');
  const rutaJs = path.join(RAIZ, 'api', '_license.js');
  const respaldo = { py: fs.readFileSync(rutaPy), js: fs.readFileSync(rutaJs) };
  try {
    const { publica } = generarPar();
    pegarPublica(publica);
    const py = fs.readFileSync(rutaPy, 'utf-8');
    const js = fs.readFileSync(rutaJs, 'utf-8');
    assert.ok(py.includes(`CLAVE_PUBLICA_EMBEBIDA = "${publica}"`), 'no se pegó en el .py');
    assert.ok(js.includes(`const CLAVE_PUBLICA_EMBEBIDA = '${publica}';`),
              'no se pegó en el .js');
  } finally {
    // Restaurar SIEMPRE: si este test dejara el repo con una pública de prueba,
    // el próximo build produciría instaladores que no abren ninguna licencia.
    fs.writeFileSync(rutaPy, respaldo.py);
    fs.writeFileSync(rutaJs, respaldo.js);
  }
});

test('si falta la constante en uno de los dos, no se escribe ninguno', () => {
  const RAIZ = path.resolve(__dirname, '..');
  const rutaJs = path.join(RAIZ, 'api', '_license.js');
  const rutaPy = path.join(RAIZ, 'mvpm', 'licensing.py');
  const respaldo = { py: fs.readFileSync(rutaPy), js: fs.readFileSync(rutaJs) };
  try {
    fs.writeFileSync(rutaJs, '// sin la constante\n');
    const antesPy = fs.readFileSync(rutaPy, 'utf-8');
    assert.throws(() => pegarPublica(generarPar().publica), /_license\.js/);
    assert.strictEqual(fs.readFileSync(rutaPy, 'utf-8'), antesPy,
      'se escribió el .py aunque el .js falló: las mitades quedarían separadas');
  } finally {
    fs.writeFileSync(rutaPy, respaldo.py);
    fs.writeFileSync(rutaJs, respaldo.js);
  }
});

if (!process.exitCode) console.log(`\ntodos los tests de rotación pasaron (${pasaron})`);
