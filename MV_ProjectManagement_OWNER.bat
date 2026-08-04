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
rem se puede activar nada (antes alcanzaba con que el archivo existiera, o sea
rem que cualquier cliente se saltaba el candado creandolo a mano).
rem
rem No hay nada que configurar a mano: activar_owner.py resuelve la clave solo
rem —variable de entorno, el archivo donde la dejo la primera vez, o la genera
rem si esto es una copia del repositorio— y activa. Una sola vez por maquina.
"%PY%" packaging\activar_owner.py
if errorlevel 1 (
    echo.
    echo No se pudo activar. Si es una instalacion de cliente, usa el
    echo instalador Owner Edition, que ya trae el modo dueno adentro.
    echo Si faltan dependencias, corre antes MV_ProjectManagement.bat una vez.
    pause
    exit /b 1
)

echo.
pause
