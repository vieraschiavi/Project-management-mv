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
; Acceso directo en el menú Inicio / lista de programas de Windows (siempre).
; {autoprograms} respeta lo elegido en la pantalla de per-user/per-machine.
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Acceso directo en el escritorio — MARCADO por defecto: es lo que el usuario
; espera de un programa de escritorio, y puede desmarcarlo si no lo quiere.
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[CustomMessages]
spanish.UnidadInvalida=La unidad seleccionada no existe o no está disponible.%n%nElegí una carpeta en un disco conectado (por ejemplo C:\ o D:\).
english.UnidadInvalida=The selected drive does not exist or is not available.%n%nChoose a folder on a connected disk (for example C:\ or D:\).
spanish.SinEspacio=No hay espacio suficiente en %1%n%nLibre: %2 MB — hacen falta al menos %3 MB.%n%nElegí otra carpeta o liberá espacio.
english.SinEspacio=Not enough space on %1%n%nFree: %2 MB — at least %3 MB are required.%n%nChoose another folder or free up space.
spanish.SinPermiso=No se puede escribir en:%n%1%n%nElegí otra carpeta, o volvé atrás y marcá "instalar sólo para mí" para instalar en tu perfil de usuario sin permisos de administrador.
english.SinPermiso=Cannot write to:%n%1%n%nChoose another folder, or go back and select "install for me only" to install into your user profile without administrator rights.

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
{ Validación de la carpeta de instalación.

  Sin esto, elegir un disco que no existe (una letra de una unidad USB que se
  desconectó), uno sin espacio, o una carpeta protegida como Archivos de
  programa sin ser administrador, dejaba que el asistente avanzara y recién
  fallara al copiar — con un error genérico de Windows que no dice qué hacer.
  Acá se comprueba en la misma pantalla donde se elige, y el mensaje dice cuál
  es el problema y cómo resolverlo. }

const
  MB = 1048576;
  { El .exe onefile de PyInstaller ronda los 120 MB y se descomprime en disco
    al correr; se pide margen para eso y para la base SQLite. }
  ESPACIO_MINIMO_MB = 400;

function CarpetaExistenteMasCercana(Dir: String): String;
begin
  { Se sube hasta encontrar algo que exista: la carpeta elegida puede no haber
    sido creada todavía, pero su unidad o su carpeta padre sí. }
  Result := RemoveBackslashUnlessRoot(Dir);
  while (Result <> '') and not DirExists(Result) do
    Result := RemoveBackslashUnlessRoot(ExtractFileDir(Result));
end;

function UnidadDisponible(Dir: String): Boolean;
var
  Unidad: String;
begin
  Unidad := ExtractFileDrive(Dir);
  { Rutas de red (\\servidor\recurso) no tienen letra: se dejan pasar y que
    decida el chequeo de escritura, que es el que importa. }
  if (Unidad = '') or (Copy(Dir, 1, 2) = '\\') then
    Result := True
  else
    Result := DirExists(Unidad + '\');
end;

function EspacioLibreMB(Dir: String): Int64;
var
  Libre, Total: Int64;
begin
  if GetSpaceOnDisk64(CarpetaExistenteMasCercana(Dir), Libre, Total) then
    Result := Libre div MB
  else
    Result := -1;  { no se pudo averiguar: no se bloquea por las dudas }
end;

function SePuedeEscribir(Dir: String): Boolean;
var
  Prueba: String;
  CreamosLaCarpeta: Boolean;
begin
  CreamosLaCarpeta := not DirExists(Dir);
  if CreamosLaCarpeta and not ForceDirectories(Dir) then begin
    Result := False;
    Exit;
  end;

  Prueba := AddBackslash(Dir) + 'mvpm_prueba_escritura.tmp';
  Result := SaveStringToFile(Prueba, 'mvpm', False);
  if Result then
    DeleteFile(Prueba);

  { Si la carpeta la creamos para probar y la instalación no sigue, no se deja
    tirada una carpeta vacía en la máquina del usuario. }
  if CreamosLaCarpeta then
    RemoveDir(Dir);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Libre: Int64;
begin
  Result := True;
  if CurPageID <> wpSelectDir then
    Exit;

  if not UnidadDisponible(WizardDirValue) then begin
    MsgBox(CustomMessage('UnidadInvalida'), mbError, MB_OK);
    Result := False;
    Exit;
  end;

  Libre := EspacioLibreMB(WizardDirValue);
  if (Libre >= 0) and (Libre < ESPACIO_MINIMO_MB) then begin
    MsgBox(FmtMessage(CustomMessage('SinEspacio'),
                      [ExtractFileDrive(WizardDirValue),
                       IntToStr(Libre), IntToStr(ESPACIO_MINIMO_MB)]),
           mbError, MB_OK);
    Result := False;
    Exit;
  end;

  if not SePuedeEscribir(WizardDirValue) then begin
    MsgBox(FmtMessage(CustomMessage('SinPermiso'), [WizardDirValue]),
           mbError, MB_OK);
    Result := False;
  end;
end;
