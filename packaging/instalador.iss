; Script de Inno Setup 6 — compila el instalador MVProjectManagement_Setup_vX.exe
; a partir del build de PyInstaller. Se compila en CI (ver
; .github/workflows/build_windows.yml), no requiere nada de parte del usuario
; final más que doble clic.

#define MyAppName "MV Project Management"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "MV"
#define MyAppExeName "MVProjectManagement.exe"

[Setup]
AppId={{B8E2C4A0-6F1A-4B7E-9C3D-MVPM00000001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
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

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\MVProjectManagement\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

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
