@echo off
setlocal
title MV Project Management - Activar modo dueno
cd /d "%~dp0"

echo ============================================
echo   MV Project Management - Modo DUENO
echo ============================================
echo.
echo Marca ESTA maquina como la del dueno del producto: el programa
echo corre sin el candado de la prueba de 7 dias, se abra como se abra
echo (MV_ProjectManagement.bat, run.sh, el .exe o streamlit directo).
echo.
echo Se escribe un archivo en tus datos de usuario, no en la carpeta del
echo programa: no se puede colar en un ZIP ni en un instalador de cliente.
echo.

rem Se usa el Python del entorno virtual si ya existe (lo crea el .bat
rem principal la primera vez); si no, el Python del sistema.
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

rem El marcador es un token FIRMADO con la clave privada del dueno: sin ella no
rem se puede activar nada. Antes alcanzaba con que el archivo existiera, o sea
rem que cualquier cliente se saltaba el candado creandolo a mano.
rem
rem La forma NORMAL de tener el modo dueno hoy es el instalador Owner Edition:
rem trae el marcador ya firmado adentro, asi que se instala y listo, sin tocar
rem ninguna variable. Este .bat queda como alternativa para quien prefiera
rem activarlo sobre una instalacion portable que ya tiene.
if "%MVPM_LICENSE_PRIVATE_KEY%"=="" (
    echo No hace falta este .bat: usa el INSTALADOR Owner Edition.
    echo.
    echo   MVProjectManagementOwner_Setup_v0.2.0.exe
    echo.
    echo Ese instalador trae el modo dueno ya firmado adentro: lo instalas,
    echo abris el programa y ya corre sin el candado de los 7 dias. No hay que
    echo configurar ninguna variable ni abrir una consola.
    echo.
    echo Donde bajarlo: en GitHub, pestana Actions, workflow
    echo "Build Windows installer (Owner Edition)" - Run workflow. Al terminar
    echo queda como artefacto de esa corrida. Con un tag owner-v* ademas queda
    echo publicado como Release del repo.
    echo.
    echo ---------------------------------------------------------------
    echo Alternativa avanzada: activarlo sobre ESTA carpeta portable.
    echo Necesitas la clave privada de licencias:
    echo     set MVPM_LICENSE_PRIVATE_KEY=^<tu-clave^>
    echo     MV_ProjectManagement_OWNER.bat
    echo Si todavia no generaste el par de claves:
    echo     python packaging\generar_claves_licencia.py --escribir
    pause
    exit /b 1
)

"%PY%" -c "from mvpm import owner; print('OK - modo owner activado'); print('Marcador:', owner.activar())"
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo activar. Corre primero MV_ProjectManagement.bat
    echo una vez para que instale las dependencias.
    pause
    exit /b 1
)

echo.
echo Listo. Abri MV_ProjectManagement.bat normalmente: ya no te va a
echo pedir licencia. Para volver atras, borra el archivo que dice
echo "Marcador:" mas arriba.
echo.
pause
