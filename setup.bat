@echo off
chcp 65001 >nul
title Rugdraiger Downloader — Setup
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   RUGDRAIGER DOWNLOADER — INSTALACION    ║
echo  ╚══════════════════════════════════════════╝
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.11+ desde python.org
    pause
    exit /b 1
)

echo [1/4] Creando entorno virtual...
if not exist ".venv" python -m venv .venv

echo [2/4] Instalando dependencias Python...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/4] Descargando yt-dlp...
if not exist "bin" mkdir bin
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile 'bin\yt-dlp.exe' -UseBasicParsing"

echo [4/4] Descargando ffmpeg y Node.js (incluidos en la app)...
python scripts\fetch_runtime_deps.py
if errorlevel 1 (
    echo [AVISO] No se pudieron descargar ffmpeg/Node. La app funcionara con limitaciones.
)

echo.
echo  ═══════════════════════════════════════════
echo   Instalacion completada.
echo.
echo   ffmpeg y Node.js se empaquetan con la app.
echo   No necesitas winget ni instalaciones extra.
echo.
echo   Ejecuta run.bat para abrir la aplicacion.
echo  ═══════════════════════════════════════════
echo.
pause
