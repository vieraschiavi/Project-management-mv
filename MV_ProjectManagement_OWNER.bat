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
