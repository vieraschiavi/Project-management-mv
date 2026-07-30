; Script de Inno Setup 6 — compila el instalador MVProjectManagement_Setup_vX.exe
; a partir del build de PyInstaller. Se compila en CI (ver
; .github/workflows/build_windows.yml), no requiere nada de parte del usuario
; final más que doble clic.
;
; Comportamiento de instalador profesional, explícito (no dejado al default):
; * DisableDirPage=no        → SIEMPRE muestra "Elegir carpeta de instalación"
;   con botón Examinar, sin importar el modo (per-user o per-machine).
; * PrivilegesRequired=lowest + PrivilegesRequiredOverridesAllowed=dialog →
;   el asistente pregunta "¿instalar solo para mí o para todos los usuarios
;   de esta PC?". Sin admin, se instala igual en el perfil del usuario
;   (necesario en notebooks de empresa donde el empleado no es admin local).
;   {autopf} más abajo resuelve solo a Program Files o al equivalente
;   por-usuario según lo que elija acá — no hace falta if/else manual.

#define MyAppName "MV Project Management"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "MV"
#define MyAppPublisherEmail "vieraschiavi@gmail.com"
#define MyAppExeName "MVProjectManagement.exe"

[Setup]
AppId={{B8E2C4A0-6F1A-4B7E-9C3D-MVPM00000001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=mailto:{#MyAppPublisherEmail}
AppSupportURL=mailto:{#MyAppPublisherEmail}
AppContact={#MyAppPublisherEmail}
DefaultDirName={autopf}\MV Project Management
DefaultGroupName={#MyAppName}
OutputBaseFilename=MVProjectManagement_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
DisableProgramGroupPage=yes
; Página de destino SIEMPRE visible — es lo que pide "elegir dónde instalar".
DisableDirPage=no
DisableReadyPage=no
; Deja elegir instalación por-usuario (sin admin) o para toda la PC (con
; admin), con {autopf}/{autodesktop}/{autoprograms} resolviendo solo según
; lo que el usuario elija en esa pantalla.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Ficha "Detalles" del .exe en Explorador (clic derecho → Propiedades).
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} — instalador
VersionInfoProductName={#MyAppName}
VersionInfoCopyright=© {#MyAppPublisher}
; No instala nada raro si algún día se firma el binario, pero no lo asumimos.
AllowNoIcons=yes
; Página obligatoria de aceptación del EULA — sin marcar "Acepto" no se
; puede avanzar. El texto se compila DENTRO del instalador (no requiere
; un archivo aparte junto al .exe final).
LicenseFile=EULA.txt

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; PyInstaller compila en modo onefile → un único .exe (no una carpeta).
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Acceso directo en el menú Inicio / barra de programas (siempre)
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Acceso directo en el escritorio (opcional — el cliente marca la casilla)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
