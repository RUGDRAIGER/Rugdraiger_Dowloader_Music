@echo off
chcp 65001 >nul
title Rugdraiger Downloader — Build Instalador
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-installer.ps1"
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo la compilacion del instalador.
    pause
    exit /b 1
)
pause
