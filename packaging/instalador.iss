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
; Carpeta que deja PyInstaller en dist\ (el `name=` del COLLECT en
; packaging/mvpm.spec). Es lo que se empaqueta, no un archivo suelto.
#define MyAppDirName "MVProjectManagement"

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
; PyInstaller compila en modo onedir → una CARPETA (dist\MVProjectManagement\)
; con el .exe y sus dependencias al lado, no un único archivo.
;
; Era onefile, y ahí el .exe se descomprimía entero a %TEMP% en cada arranque.
; Eso fallaba de verdad en la máquina de un usuario ("Failed to extract
; mvpm\policies.cp311-win_amd64.pyd: decompression resulted in return code
; -1!") y, además, escribía ~300-400 MB en C: aunque el programa estuviera
; instalado en otro disco — ver el comentario largo en packaging/mvpm.spec.
;
; Para el usuario no cambia nada: sigue recibiendo un solo instalador y un
; solo acceso directo. Lo que cambia es que ahora los archivos viven en la
; carpeta que eligió y no hay descompresión en cada arranque.
Source: "..\dist\{#MyAppDirName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

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
  { La carpeta de onedir ronda los 350 MB ya descomprimida; se pide margen
    para eso y para la base SQLite.

    Con onefile este número medía el disco equivocado: los archivos se
    descomprimían a %TEMP% (siempre en C:), así que validar espacio en la
    carpeta elegida no decía nada sobre dónde iba a fallar de verdad. Ahora
    los archivos SÍ viven donde el usuario eligió, y este chequeo mide ese
    mismo disco. }
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
  Detalles: array of String;
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
    { El literal de array NO puede quedar como primer carácter no-blanco de
      una línea: el preprocesador de Inno lee línea por línea buscando
      encabezados de sección, y un '[' al principio de renglón lo confunde
      con un "[NombreDeSección]" — "Invalid section tag", compilación
      abortada. Por eso se arma en una variable en vez de en la llamada. }
    Detalles := [ExtractFileDrive(WizardDirValue), IntToStr(Libre),
                IntToStr(ESPACIO_MINIMO_MB)];
    MsgBox(FmtMessage(CustomMessage('SinEspacio'), Detalles), mbError, MB_OK);
    Result := False;
    Exit;
  end;

  if not SePuedeEscribir(WizardDirValue) then begin
    MsgBox(FmtMessage(CustomMessage('SinPermiso'), [WizardDirValue]),
           mbError, MB_OK);
    Result := False;
  end;
end;
