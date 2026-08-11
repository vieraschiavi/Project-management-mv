@echo off
setlocal enabledelayedexpansion
title MV Project Management
cd /d "%~dp0"

echo ============================================
echo   MV Project Management - iniciando...
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python en el sistema.
    echo Instala Python 3.11+ desde https://www.python.org/downloads/
    echo y marca la casilla "Add python.exe to PATH" durante la instalacion.
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

if not exist ".venv\Scripts\python.exe" (
    echo Primera vez: creando entorno virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo Instalando dependencias (puede tardar un par de minutos)...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Fallo la instalacion de dependencias.
        pause
        exit /b 1
    )
)

rem Chequeo de arranque: que el motor IMPORTE. Es lo unico que puede impedir
rem que el programa abra, y tarda menos de un segundo.
rem
rem Antes aca se corria la suite entera (pytest tests\), y eso estaba mal por
rem dos motivos. Uno: tarda minutos, asi que al doble clic no pasaba nada
rem visible y parecia que el .bat no abria. Dos: varios tests verifican cosas
rem del REPOSITORIO (.github\, landing\, distribucion\, owner\) que no viajan
rem en el paquete, asi que en la copia del usuario fallaban siempre - y uno
rem cortaba la coleccion entera. El usuario abria su programa y lo primero que
rem veia era una pared de errores rojos de tests que no son asunto suyo.
echo Verificando instalacion...
".venv\Scripts\python.exe" -c "import mvpm, streamlit, pandas" 2>nul
if errorlevel 1 (
    echo [ERROR] Faltan dependencias o quedaron a medio instalar.
    echo Borra la carpeta .venv y volve a ejecutar este archivo.
    pause
    exit /b 1
)

rem Puerto: se elige uno libre en vez de dejar que Streamlit tome su 8501 por
rem defecto. Ese es el puerto mas disputado (cualquier otra app de Streamlit
rem abierta lo tiene), y el programa moria con "Address already in use" o se
rem quedaba pegado a la app ajena. mvpm\puertos.py decide, igual que el .exe.
for /f "delims=" %%p in ('".venv\Scripts\python.exe" -m mvpm.puertos') do set "MVPM_PUERTO=%%p"
if not defined MVPM_PUERTO set "MVPM_PUERTO=8731"

echo.
echo Abriendo MV Project Management...
echo   http://localhost:%MVPM_PUERTO%

rem Ventana propia del programa, no una pestana mas del navegador abierto.
rem mvpm\ventana.py usa el modo aplicacion de Edge/Chrome: sin barra de
rem direcciones ni pestanas, con su propio icono en la barra de tareas. Si no
rem encuentra ninguno cae solo a la pestana comun. Va en segundo plano porque
rem espera a que Streamlit escuche, y Streamlit arranca en la linea siguiente.
start "" /b ".venv\Scripts\python.exe" -m mvpm.ventana "http://localhost:%MVPM_PUERTO%"

".venv\Scripts\python.exe" -m streamlit run app\app.py --server.headless true --server.port %MVPM_PUERTO%

pause
