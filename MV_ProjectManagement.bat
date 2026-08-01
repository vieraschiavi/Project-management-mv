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

echo Verificando instalacion...
".venv\Scripts\python.exe" -m pytest tests\ -q --no-header
if errorlevel 1 (
    echo [ADVERTENCIA] Algunos tests fallaron, pero se intenta igual iniciar el programa.
)

rem Puerto: se elige uno libre en vez de dejar que Streamlit tome su 8501 por
rem defecto. Ese es el puerto mas disputado (cualquier otra app de Streamlit
rem abierta lo tiene), y el programa moria con "Address already in use" o se
rem quedaba pegado a la app ajena. mvpm\puertos.py decide, igual que el .exe.
for /f "delims=" %%p in ('".venv\Scripts\python.exe" -m mvpm.puertos') do set "MVPM_PUERTO=%%p"
if not defined MVPM_PUERTO set "MVPM_PUERTO=8731"

echo.
echo Abriendo MV Project Management en tu navegador...
echo   http://localhost:%MVPM_PUERTO%
start "" "http://localhost:%MVPM_PUERTO%"
".venv\Scripts\python.exe" -m streamlit run app\app.py --server.headless true --server.port %MVPM_PUERTO%

pause
