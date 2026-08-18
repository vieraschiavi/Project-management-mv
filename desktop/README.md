# MV Project Management — versión de escritorio (Electron)

Envuelve el mismo motor Python/Streamlit en una ventana nativa — ícono
propio, sin barra de navegador, sin pestaña del sistema — en vez de abrir
el navegador por defecto, que es lo que hace hoy el instalador Python solo.
**No reescribe ninguna pantalla**: la UI sigue siendo la misma app de
Streamlit, corriendo embebida como proceso hijo dentro de la ventana de
Electron.

## Desarrollo local

Requiere tener el proyecto Python funcionando (`../run.sh install` primero).

```bash
npm install
npm start
```

En desarrollo, Electron corre `python3 packaging/mvpm_launcher.py`
directamente — necesita Python instalado, igual que `./run.sh app`.

## Compilar el instalador real (`.exe`)

El instalador empaquetado **no necesita Python instalado en la PC del
usuario** — bundlea el ejecutable que ya produce PyInstaller
(`packaging/mvpm.spec`). Por eso el build real corre en CI, en un runner
Windows (ver `.github/workflows/build_electron.yml`), disparado por el
mismo tag `vX.Y.Z` que compila el instalador Python/Inno Setup:

```powershell
pyinstaller packaging/mvpm.spec --distpath dist --workpath build --noconfirm
# PyInstaller compila en onedir: deja una CARPETA, no un .exe suelto. El .exe
# necesita a sus dependencias al lado, así que se copia entera.
Copy-Item -Recurse -Force dist/MVProjectManagement desktop/resources/motor
cd desktop
npm ci
npm run dist   # genera desktop/release/*.exe
```

`npm run dist` corre primero `verificar_motor.js`, que aborta si
`resources/motor/MVProjectManagement.exe` no está. No es un chequeo de más:
electron-builder, ante un `extraResources` que no existe, sólo avisa
—`file source doesn't exist`— y **arma el instalador igual**. Ese instalador
pesa poco, instala bien, y al abrirlo muestra "No se encontró el motor de la
aplicación": una ventana vacía. Falla en la PC del cliente, no en el build.

## Cómo lo instala el usuario

El asistente pregunta todo, no instala a ciegas:

1. **Para quién**: sólo para mí (no necesita ser administrador — importa en
   notebooks de empresa) o para todos los usuarios de la PC.
2. **Dónde**: pantalla de destino con botón Examinar. **Se puede instalar en
   D:, E: o donde haya lugar.**
3. Accesos directos en el escritorio y en el menú Inicio.
4. Queda en *Agregar o quitar programas* como **MV Project Management**, con
   su desinstalador.

### La carpeta que propone no es siempre C:

`installer.nsh` mira los discos **fijos** de la PC y propone por defecto el que
más espacio libre tiene. El programa ocupa unos 400 MB —lleva el motor de
Python entero adentro— y en una notebook con el C: chico eso es justo lo que no
entra; en una PC con C: y D: la sugerencia sale sola en D:.

Tres cosas que hace a propósito:

- **Es sólo una sugerencia.** La pantalla de destino se muestra igual y
  Examinar sigue mandando.
- **No sugiere unidades removibles ni de red** (sólo `DRIVE_FIXED`): instalar
  en un pendrive que después se desconecta es peor que instalar en C:.
- **No mueve una instalación existente.** Si ya está instalado, se reinstala
  donde estaba. Reinstalar en otro disco y dejar la copia vieja tirada es un
  bug que este producto ya tuvo una vez, en el instalador owner.

Si algo de esa detección falla, el instalador sigue funcionando con el default
de electron-builder: no hay ninguna rama que aborte la instalación.

## De dónde se baja el `.exe`

Hoy el instalador de escritorio **no está publicado en ningún lado estable**:
el workflow lo sube como artefacto de cada corrida y sólo lo adjunta a un
release cuando el push es de un tag `vX.Y.Z`. Mientras no haya un tag nuevo, se
baja así:

1. GitHub → pestaña **Actions** → workflow *Build Electron desktop installer*.
2. La última corrida verde sobre `main`.
3. Artefacto **MVProjectManagement-Desktop-Windows** (es un `.zip`; adentro
   está el `.exe`).

Para publicarlo en un release, hay que taguear:

```bash
git tag v0.2.0 && git push origin v0.2.0
```

## Por qué existe además del instalador Python/Inno Setup

Son dos instaladores Windows con el mismo motor adentro — se publican los
dos en el mismo release:

- **`MVProjectManagement_Setup_vX.Y.Z.exe`** (PyInstaller + Inno Setup): más
  liviano, abre el programa en el navegador del sistema.
- **`MVProjectManagement-Desktop-Setup-X.Y.Z.exe`** (este, Electron): ventana
  nativa propia, sin barra de navegador — la experiencia de escritorio más
  "profesional", a costa de un instalador más pesado (incluye Electron).
