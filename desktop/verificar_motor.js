// © 2026 Martín Viera. Todos los derechos reservados.
//
// Corre ANTES de electron-builder (ver "dist" en package.json) y aborta si el
// motor Python no está en su lugar.
//
// Por qué hace falta: `extraResources` copia resources/motor adentro del
// instalador, pero si esa carpeta no existe electron-builder sólo avisa
//
//     • file source doesn't exist  from=.../desktop/resources/motor
//
// y sigue de largo. El resultado es un instalador que pesa poco, instala bien,
// y al abrirse muestra "No se encontró el motor de la aplicación" — la ventana
// de Electron sin nada adentro. Un fallo así no se nota en el build: se nota
// en la PC del cliente.
//
// La carpeta la produce el paso de PyInstaller de .github/workflows/
// build_electron.yml; en local se arma con:
//
//     pyinstaller packaging/mvpm.spec --distpath dist --workpath build --noconfirm
//     cp -r dist/MVProjectManagement desktop/resources/motor

const fs = require("fs");
const path = require("path");

const MOTOR = path.join(__dirname, "resources", "motor");
// El .exe que arranca main.js: path.join(process.resourcesPath, "motor", EXE).
// Se verifica el ejecutable y no sólo la carpeta, porque una copia a medias
// deja la carpeta creada y el instalador saldría igual de roto.
const EXE = "MVProjectManagement.exe";

function fallar(mensaje) {
  console.error("\n  ✗ No se puede armar el instalador de escritorio.\n");
  console.error(`    ${mensaje}\n`);
  console.error("    El motor lo produce PyInstaller. Para armarlo:\n");
  console.error("      pyinstaller packaging/mvpm.spec --distpath dist "
    + "--workpath build --noconfirm");
  console.error("      cp -r dist/MVProjectManagement desktop/resources/motor\n");
  process.exit(1);
}

if (!fs.existsSync(MOTOR)) {
  fallar(`Falta la carpeta del motor: ${MOTOR}`);
}

const exe = path.join(MOTOR, EXE);
if (!fs.existsSync(exe)) {
  const hay = fs.readdirSync(MOTOR).slice(0, 10).join(", ") || "(vacía)";
  fallar(`La carpeta del motor existe pero no tiene ${EXE}.\n`
    + `    ${MOTOR} contiene: ${hay}`);
}

const tamano = fs.statSync(exe).size;
if (tamano < 1024) {
  fallar(`${EXE} pesa ${tamano} bytes — la copia quedó truncada.`);
}

console.log(`  ✓ Motor encontrado: ${exe}`);
