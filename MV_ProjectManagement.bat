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

echo.
echo Abriendo MV Project Management en tu navegador...
".venv\Scripts\python.exe" -m streamlit run app\app.py --server.headless true

pause
