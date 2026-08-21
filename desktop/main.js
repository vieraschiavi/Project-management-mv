// © 2026 Martín Viera. Todos los derechos reservados.
//
// Proceso principal de Electron.
//
// ## Qué cambió: Streamlit adentro, React adentro
//
// Antes esta ventana envolvía Streamlit: era un navegador sin barra mostrando
// la misma página que se abre con `./run.sh app`. Funcionaba, pero el techo
// era el de Streamlit — nunca se iba a ver como un producto a medida, y eso
// era lo que bajaba la nota de interfaz.
//
// Ahora levanta `api/main.py` (FastAPI), que sirve la interfaz React en
// `/app`. El motor de dominio (`mvpm/`) es EXACTAMENTE el mismo: son dos
// formas de ver lo mismo, no dos productos.
//
//   .exe instalado -> React sobre la API
//   .bat portable  -> Streamlit
//
// La lógica de arranque vive en `lib/server-manager.js`, separada a propósito
// para poder testearla con Node puro: el runtime de Electron no se puede bajar
// en todos los entornos de CI, y sin esa separación la parte que más se rompe
// —encontrar el Python correcto, esperar al servidor, matarlo bien— quedaría
// sin ningún test.

const { app, BrowserWindow, dialog, shell } = require('electron');
const path = require('node:path');

const {
  puertoLibre, elegirPython, raizServidor, lanzarApi, lanzarMotorEmpaquetado,
  motorEmpaquetado, puertoAnunciado, esperarServidor, detener,
} = require('./lib/server-manager');

let ventana = null;
let servidor = null;

/** Dónde está el bundle de React, según sea instalación o desarrollo. */
function dirUi() {
  return app.isPackaged
    ? path.join(process.resourcesPath, 'ui')
    : path.join(__dirname, 'ui', 'dist');
}

function fallar(titulo, detalle) {
  dialog.showErrorBox(titulo, detalle);
  app.quit();
}

async function arrancar() {
  const pedido = await puertoLibre();
  let puerto = pedido;

  // Dos formas de levantar el MISMO motor, según dónde estemos:
  //
  //   instalado    -> el .exe de PyInstaller en modo API. Lleva `mvpm/`
  //                   compilado a .pyd y no necesita Python en la PC.
  //   desarrollo   -> uvicorn contra el código fuente del repositorio.
  //
  // El orden importa: si estuviera al revés, en una máquina de desarrollo con
  // un .exe viejo en resources/ se probaría ese y no el código que se está
  // editando.
  const exe = app.isPackaged ? motorEmpaquetado(process.resourcesPath) : null;
  if (exe) {
    servidor = lanzarMotorEmpaquetado(exe, pedido, dirUi());
    // El motor puede haber tomado OTRO puerto si el pedido se ocupó en el
    // medio: se escucha el que anuncia en vez de asumir el que se pidió.
    puerto = await puertoAnunciado(servidor, pedido);
  } else {
    const raizRepo = path.join(__dirname, '..');
    const raiz = raizServidor(app.isPackaged ? process.resourcesPath : null, raizRepo);
    const python = elegirPython(raiz);
    if (!python) {
      fallar('No encontré el motor',
        'MV Project Management no pudo encontrar ni el motor empaquetado ni un '
        + 'Python con fastapi y uvicorn.\n\n'
        + 'Si instalaste el programa desde el .exe, esto no debería pasar: '
        + 'escribinos a vieraschiavi@gmail.com.\n\n'
        + `Carpeta consultada:\n${raiz}`);
      return;
    }
    // uvicorn con --port no negocia: o toma ese puerto o falla.
    servidor = lanzarApi(python, raiz, pedido, dirUi());
  }

  // El stderr del servidor va a la consola del proceso principal a propósito:
  // si el arranque falla, el motivo real está ahí y no en el timeout genérico.
  servidor.stderr.on('data', (d) => process.stderr.write(`[motor] ${d}`));
  servidor.on('exit', (code) => {
    if (code !== 0 && !app.isQuiting) {
      fallar('El motor se cerró',
        `El servidor local terminó con código ${code}. Volvé a abrir el `
        + 'programa; si sigue pasando, escribinos a vieraschiavi@gmail.com.');
    }
  });

  ventana = new BrowserWindow({
    width: 1360,
    height: 880,
    minWidth: 960,
    minHeight: 620,
    show: false,
    backgroundColor: '#F7F9F5',
    title: 'MV Project Management',
    icon: path.join(__dirname, '..', 'packaging', 'assets', 'icon.ico'),
    webPreferences: {
      // La ventana carga http://127.0.0.1 y nada más. Sin `nodeIntegration` y
      // con `contextIsolation`, aunque alguien lograra inyectar algo en la
      // interfaz, no tendría acceso al sistema de archivos ni a `require`.
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });
  ventana.setMenuBarVisibility(false);

  // Un enlace externo abre el navegador del sistema, no esta ventana: si se
  // abriera acá, el usuario quedaría con una página web dentro de su programa
  // y sin barra de navegación para volver.
  ventana.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  const listo = await esperarServidor(puerto);
  if (!listo) {
    fallar('El motor no respondió',
      'El servidor local no llegó a levantar. Suele ser un antivirus '
      + 'bloqueando el proceso o el puerto.\n\n'
      + 'Escribinos a vieraschiavi@gmail.com si vuelve a pasar.');
    return;
  }

  // La barra final importa: sin ella StaticFiles responde un 307 hacia `/app/`
  // y la ventana muestra un parpadeo de redirección en cada arranque.
  await ventana.loadURL(`http://127.0.0.1:${puerto}/app/`);
  ventana.show();
}

app.whenReady().then(arrancar);

// Una sola instancia: dos ventanas serían dos servidores sobre la MISMA base
// SQLite, y la segunda escritura pisaría a la primera sin avisar.
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (ventana) {
      if (ventana.isMinimized()) ventana.restore();
      ventana.focus();
    }
  });
}

app.on('window-all-closed', () => {
  app.isQuiting = true;
  detener(servidor);
  servidor = null;
  app.quit();
});

// Red de seguridad: si Electron se va por una excepción o una señal, el
// `window-all-closed` de arriba puede no llegar a correr y el Python quedaría
// vivo ocupando el puerto y la base.
app.on('before-quit', () => { app.isQuiting = true; detener(servidor); });
process.on('exit', () => detener(servidor));
