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
Copy-Item dist/MVProjectManagement.exe desktop/resources/MVProjectManagement.exe
cd desktop
npm ci
npm run dist   # genera desktop/release/*.exe
```

## Por qué existe además del instalador Python/Inno Setup

Son dos instaladores Windows con el mismo motor adentro — se publican los
dos en el mismo release:

- **`MVProjectManagement_Setup_vX.Y.Z.exe`** (PyInstaller + Inno Setup): más
  liviano, abre el programa en el navegador del sistema.
- **`MVProjectManagement-Desktop-Setup-X.Y.Z.exe`** (este, Electron): ventana
  nativa propia, sin barra de navegador — la experiencia de escritorio más
  "profesional", a costa de un instalador más pesado (incluye Electron).
