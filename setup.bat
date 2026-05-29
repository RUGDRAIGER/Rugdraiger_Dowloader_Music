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

echo [1/3] Creando entorno virtual...
if not exist ".venv" python -m venv .venv

echo [2/3] Instalando dependencias Python...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] Descargando yt-dlp...
if not exist "bin" mkdir bin
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile 'bin\yt-dlp.exe' -UseBasicParsing"

echo.
echo  ═══════════════════════════════════════════
echo   Instalacion completada.
echo.
echo   IMPORTANTE — Para maxima calidad instala tambien:
echo   • ffmpeg  → winget install Gyan.FFmpeg
echo   • Node.js → winget install OpenJS.NodeJS.LTS
echo     (necesario para desafios JS de YouTube)
echo.
echo   Ejecuta run.bat para abrir la aplicacion.
echo  ═══════════════════════════════════════════
echo.
pause
