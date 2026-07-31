; Script de Inno Setup 6 — "Owner Edition". Mismo instalador profesional que
; packaging/instalador.iss (icono en Menú Inicio + escritorio, elegir
; carpeta, elegir per-user/per-machine, EULA), con dos diferencias:
;   1. Empaqueta el .exe compilado desde mvpm_owner.spec (trae el marcador
;      OWNER_EDITION → arranca con MVPM_OWNER_BYPASS=1, sin candado de 7
;      días ni límite de cupo de IA).
;   2. AppId, nombre de carpeta y nombre de .exe distintos — para poder
;      tener instalada la versión Owner y la versión cliente en la misma
;      PC al mismo tiempo, sin que una pise a la otra.
;
; Se compila SOLO en .github/workflows/build_windows_owner.yml (disparo
; manual o tag owner-v*), nunca en build_windows.yml — y el resultado se
; sube como artefacto/Release de GitHub, jamás a Vercel Blob ni linkeado
; desde la landing pública.

#define MyAppName "MV Project Management (Owner)"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "MV"
#define MyAppPublisherEmail "vieraschiavi@gmail.com"
#define MyAppExeName "MVProjectManagementOwner.exe"

[Setup]
AppId={{B8E2C4A0-6F1A-4B7E-9C3D-MVPM0000OWNR}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=mailto:{#MyAppPublisherEmail}
AppSupportURL=mailto:{#MyAppPublisherEmail}
AppContact={#MyAppPublisherEmail}
DefaultDirName={autopf}\MV Project Management Owner
DefaultGroupName={#MyAppName}
OutputBaseFilename=MVProjectManagementOwner_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=no
DisableReadyPage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} — instalador
VersionInfoProductName={#MyAppName}
VersionInfoCopyright=© {#MyAppPublisher}
AllowNoIcons=yes
LicenseFile=EULA.txt

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
