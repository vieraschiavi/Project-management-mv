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

rem Destino: se puede pasar como argumento para elegir carpeta o disco.
rem   INSTALAR_OWNER.bat "D:\Programas\MV Owner"
set "DESTINO=%~1"
if "%DESTINO%"=="" set "DESTINO=%LOCALAPPDATA%\MV Project Management Owner"

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

:ACCESO
rem WindowStyle 7 = minimizada: la consola del lanzador no se planta en
rem pantalla, y el programa abre en su propia ventana (mvpm\ventana.py).
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%~1'); $s.TargetPath = '%LANZADOR%'; $s.WorkingDirectory = '%DESTINO%'; $s.WindowStyle = 7; $s.Description = 'MV Project Management - Owner Edition'; if (Test-Path '%ICONO%') { $s.IconLocation = '%ICONO%' }; $s.Save()" >nul 2>nul
if errorlevel 1 echo    [aviso] No se pudo crear %~1
exit /b 0
