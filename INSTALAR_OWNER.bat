@echo off
setlocal enabledelayedexpansion
title MV Project Management (Owner) - Instalador
cd /d "%~dp0"

echo ==================================================
echo   MV Project Management - Owner Edition
echo   Instalador
echo ==================================================
echo.

rem --------------------------------------------------------------------
rem Este instalador NO convierte una copia de cliente en la version owner.
rem Instala ESTE paquete, que ya es la version owner: mvpm\edicion.py viene
rem con ES_OWNER_BUILD = True desde que se armo el ZIP.
rem
rem La diferencia importa. Una herramienta que desbloquee una instalacion
rem ajena funciona igual en la maquina de cualquier cliente: seria un crack
rem del producto, no un instalador. Por eso esto copia lo que ya tiene, y
rem se niega a seguir si lo que tiene no es el paquete del dueno.
rem --------------------------------------------------------------------

if not exist "mvpm\edicion.py" (
    echo [ERROR] Este .bat tiene que correr desde adentro del paquete,
    echo         al lado de la carpeta mvpm\. No lo copies suelto.
    pause
    exit /b 1
)

findstr /C:"ES_OWNER_BUILD = True" "mvpm\edicion.py" >nul
if errorlevel 1 (
    echo [ERROR] Este paquete NO es la Owner Edition: es el de cliente.
    echo.
    echo         Instalarlo igual dejaria un programa que dice "Owner" y se
    echo         comporta como el de un cliente, con la prueba de 7 dias.
    echo         Baja owner\MV_Project_Management_OWNER.zip del repositorio.
    pause
    exit /b 1
)

rem --------------------------------------------------------------------
rem Donde instalar. Tres fuentes, en orden de prioridad:
rem
rem   1. El argumento, si se paso: INSTALAR_OWNER.bat "D:\Programas\MV Owner"
rem   2. La instalacion que YA exista en esta PC. Se detecta sola: se lee a
rem      donde apunta el acceso directo que dejo la corrida anterior.
rem   3. %LOCALAPPDATA%, que vive en C:.
rem
rem El paso 2 es el que faltaba. Sin el, quien habia instalado en D: y volvia
rem a correr esto se encontraba con una SEGUNDA instalacion en C:, con los
rem accesos directos apuntando a la nueva y la vieja quedando muerta en disco.
rem Nunca se le preguntaba nada ni se le avisaba: simplemente reaparecia en C:.
rem --------------------------------------------------------------------
set "MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "LNK_MENU=%MENU%\MV Project Management (Owner).lnk"
set "LNK_ESCRITORIO=%USERPROFILE%\Desktop\MV Project Management (Owner).lnk"

set "DESTINO=%~1"
if not "%DESTINO%"=="" goto :TIENE_DESTINO

call :DETECTAR "%LNK_MENU%"
if "%DESTINO%"=="" call :DETECTAR "%LNK_ESCRITORIO%"
if "%DESTINO%"=="" goto :SIN_PREVIA

echo Se detecto una instalacion anterior y se va a reinstalar ahi mismo,
echo en el disco que ya habias elegido:
echo   %DESTINO%
echo.
goto :TIENE_DESTINO

:SIN_PREVIA
set "DESTINO=%LOCALAPPDATA%\MV Project Management Owner"

:TIENE_DESTINO
echo Se va a instalar en:
echo   %DESTINO%
echo.
echo (Para elegir otra carpeta, cerra esto y arrastra la carpeta destino
echo  sobre este archivo, o corre: INSTALAR_OWNER.bat "D:\ruta\que\quieras")
echo.
pause

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python en el sistema.
    echo Instala Python 3.11+ desde https://www.python.org/downloads/
    echo y marca "Add python.exe to PATH" durante la instalacion.
    pause
    exit /b 1
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Se detecto un Python de la Microsoft Store o una version vieja.
    echo Instala Python 3.11+ desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [1/4] Copiando archivos...
if not exist "%DESTINO%" mkdir "%DESTINO%"
rem /MIR no: borraria el .venv de una instalacion previa y habria que
rem reinstalar las dependencias cada vez. Se excluyen las carpetas que se
rem regeneran solas.
robocopy "%CD%" "%DESTINO%" /E /NFL /NDL /NJH /NJS /NP /XD ".venv" "__pycache__" ".git" >nul
if errorlevel 8 (
    echo [ERROR] No se pudieron copiar los archivos a "%DESTINO%".
    echo Revisa que tengas permisos de escritura en esa carpeta.
    pause
    exit /b 1
)

echo [2/4] Preparando el entorno (puede tardar un par de minutos)...
pushd "%DESTINO%"
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        popd
        pause
        exit /b 1
    )
)
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    popd
    pause
    exit /b 1
)

rem Que el motor importe Y que la copia instalada se reconozca como owner.
rem Si esto ultimo fallara, el programa abriria con la prueba de 7 dias y el
rem instalador habria dicho que todo salio bien.
".venv\Scripts\python.exe" -c "import mvpm, streamlit, pandas" 2>nul
if errorlevel 1 (
    echo [ERROR] Faltan dependencias o quedaron a medio instalar.
    popd
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -c "from mvpm import owner; raise SystemExit(0 if owner.es_owner() else 1)"
if errorlevel 1 (
    echo [ERROR] La copia instalada NO quedo como Owner Edition.
    echo         No se crean accesos directos: preferimos cortar antes que
    echo         dejarte un icono que abre un programa con candado.
    popd
    pause
    exit /b 1
)
popd

echo [3/4] Creando accesos directos...
set "LANZADOR=%DESTINO%\MV_ProjectManagement.bat"
set "ICONO=%DESTINO%\packaging\assets\icon.ico"
set "MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
call :ACCESO "%USERPROFILE%\Desktop\MV Project Management (Owner).lnk"
call :ACCESO "%MENU%\MV Project Management (Owner).lnk"

echo [4/4] Escribiendo el desinstalador...
> "%DESTINO%\DESINSTALAR.bat" echo @echo off
>> "%DESTINO%\DESINSTALAR.bat" echo title MV Project Management (Owner) - Desinstalar
>> "%DESTINO%\DESINSTALAR.bat" echo echo Se van a borrar los accesos directos y esta carpeta:
>> "%DESTINO%\DESINSTALAR.bat" echo echo   %DESTINO%
>> "%DESTINO%\DESINSTALAR.bat" echo echo.
>> "%DESTINO%\DESINSTALAR.bat" echo echo Tus datos NO estan aca: viven en %%USERPROFILE%%\.mv_project_management
>> "%DESTINO%\DESINSTALAR.bat" echo echo y quedan intactos. Borra esa carpeta a mano si tambien los queres borrar.
>> "%DESTINO%\DESINSTALAR.bat" echo pause
>> "%DESTINO%\DESINSTALAR.bat" echo del "%USERPROFILE%\Desktop\MV Project Management (Owner).lnk" 2^>nul
>> "%DESTINO%\DESINSTALAR.bat" echo del "%MENU%\MV Project Management (Owner).lnk" 2^>nul
>> "%DESTINO%\DESINSTALAR.bat" echo echo Borrando...
>> "%DESTINO%\DESINSTALAR.bat" echo cd /d "%%TEMP%%"
rem El borrado va en un cmd aparte: este .bat vive adentro de la carpeta que
rem hay que borrar, y cmd relee el archivo despues de cada comando. Si se
rem borrara a si mismo, terminaria con "no se encuentra el archivo por lotes".
>> "%DESTINO%\DESINSTALAR.bat" echo start "" /min cmd /c "timeout /t 3 ^>nul ^& rmdir /s /q ""%DESTINO%"""
>> "%DESTINO%\DESINSTALAR.bat" echo echo Listo. La carpeta se borra en unos segundos.
>> "%DESTINO%\DESINSTALAR.bat" echo pause

echo.
echo ==================================================
echo   Instalado.
echo ==================================================
echo.
echo   Carpeta      : %DESTINO%
echo   Escritorio   : MV Project Management (Owner)
echo   Menu Inicio  : MV Project Management (Owner)
echo   Desinstalar  : %DESTINO%\DESINSTALAR.bat
echo.
echo   Abre sin candado y sin pedir clave: este paquete YA es la version
echo   owner. No lo repartas, es tu copia completa.
echo.
pause
start "" "%LANZADOR%"
exit /b 0

:DETECTAR
rem Deja en %DESTINO% la CARPETA a la que apunta un acceso directo, si esa
rem carpeta todavia existe y tiene el programa adentro.
rem
rem Un acceso directo colgado no cuenta: si el usuario borro la carpeta a
rem mano, se ignora y se sigue con la fuente siguiente. Por eso se exige que
rem exista mvpm\edicion.py y no solo la carpeta: una carpeta vacia que quedo
rem de un desinstalado a medias tampoco es una instalacion.
if not exist "%~1" exit /b 0
set "OBJETIVO="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "try { (New-Object -ComObject WScript.Shell).CreateShortcut('%~1').TargetPath } catch { }" 2^>nul`) do set "OBJETIVO=%%P"
if "%OBJETIVO%"=="" exit /b 0
rem %%~dpF da unidad+ruta con barra al final; se saca para no duplicarla.
for %%F in ("%OBJETIVO%") do set "CARPETA=%%~dpF"
if "%CARPETA%"=="" exit /b 0
if "%CARPETA:~-1%"=="\" set "CARPETA=%CARPETA:~0,-1%"
if not exist "%CARPETA%\mvpm\edicion.py" exit /b 0
set "DESTINO=%CARPETA%"
exit /b 0

:ACCESO
rem WindowStyle 7 = minimizada: la consola del lanzador no se planta en
rem pantalla, y el programa abre en su propia ventana (mvpm\ventana.py).
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%~1'); $s.TargetPath = '%LANZADOR%'; $s.WorkingDirectory = '%DESTINO%'; $s.WindowStyle = 7; $s.Description = 'MV Project Management - Owner Edition'; if (Test-Path '%ICONO%') { $s.IconLocation = '%ICONO%' }; $s.Save()" >nul 2>nul
if errorlevel 1 echo    [aviso] No se pudo crear %~1
exit /b 0
