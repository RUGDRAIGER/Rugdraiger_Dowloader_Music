@echo off
chcp 65001 >nul
title Rugdraiger Downloader Music
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Entorno no configurado. Ejecuta setup.bat primero.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python main.py
