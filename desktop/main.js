// Proceso principal de Electron — envuelve el mismo motor Python/Streamlit
// en una ventana nativa (sin barra de navegador, ícono propio) en vez de
// abrir una pestaña del navegador del sistema, que es lo que hace hoy el
// instalador Python solo. No reescribe ninguna pantalla: la UI sigue siendo
// Streamlit, corriendo embebida como proceso hijo.

const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("child_process");
const http = require("http");
const net = require("net");
const path = require("path");

let ventanaPrincipal = null;
let procesoStreamlit = null;

function puertoLibre() {
  return new Promise((resolve, reject) => {
    const servidor = net.createServer();
    servidor.unref();
    servidor.on("error", reject);
    servidor.listen(0, "127.0.0.1", () => {
      const { port } = servidor.address();
      servidor.close(() => resolve(port));
    });
  });
}

function comandoStreamlit(puerto) {
  const exeEmpaquetado = path.join(process.resourcesPath || "", "MVProjectManagement.exe");
  if (app.isPackaged) {
    // Instalador real: corre el .exe ya compilado por PyInstaller, sin
    // necesitar Python instalado en la PC del usuario.
    return { comando: exeEmpaquetado, args: [] };
  }
  // Desarrollo: corre el launcher directo con el Python del sistema.
  const raiz = path.join(__dirname, "..");
  return {
    comando: process.platform === "win32" ? "python" : "python3",
    args: [path.join(raiz, "packaging", "mvpm_launcher.py")],
  };
}

function esperarServidor(puerto, timeoutMs = 30000) {
  const inicio = Date.now();
  return new Promise((resolve, reject) => {
    const intentar = () => {
      const req = http.get({ host: "127.0.0.1", port: puerto, timeout: 1000 }, (res) => {
        res.destroy();
        resolve();
      });
      req.on("error", () => {
        if (Date.now() - inicio > timeoutMs) {
          reject(new Error("El servidor no respondió a tiempo."));
        } else {
          setTimeout(intentar, 300);
        }
      });
    };
    intentar();
  });
}

async function iniciarStreamlit() {
  const puerto = await puertoLibre();
  const { comando, args } = comandoStreamlit(puerto);

  procesoStreamlit = spawn(comando, args, {
    env: { ...process.env, MVPM_PORT: String(puerto), MVPM_ELECTRON: "1" },
    windowsHide: true,
  });

  procesoStreamlit.stdout?.on("data", (chunk) => process.stdout.write(chunk));
  procesoStreamlit.stderr?.on("data", (chunk) => process.stderr.write(chunk));

  procesoStreamlit.on("error", (err) => {
    dialog.showErrorBox(
      "No se pudo iniciar MV Project Management",
      `No se encontró el motor de la aplicación.\n\n${err.message}`
    );
    app.quit();
  });

  await esperarServidor(puerto);
  return puerto;
}

async function crearVentana() {
  let puerto;
  try {
    puerto = await iniciarStreamlit();
  } catch (err) {
    dialog.showErrorBox("MV Project Management no pudo arrancar", err.message);
    app.quit();
    return;
  }

  ventanaPrincipal = new BrowserWindow({
    width: 1400,
    height: 900,
    backgroundColor: "#081527",
    title: "MV Project Management",
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  ventanaPrincipal.loadURL(`http://127.0.0.1:${puerto}`);
  ventanaPrincipal.on("closed", () => {
    ventanaPrincipal = null;
  });
}

function detenerStreamlit() {
  if (procesoStreamlit && !procesoStreamlit.killed) {
    procesoStreamlit.kill();
  }
}

app.whenReady().then(crearVentana);

app.on("window-all-closed", () => {
  detenerStreamlit();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", detenerStreamlit);

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) crearVentana();
});
