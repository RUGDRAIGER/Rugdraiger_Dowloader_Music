$ErrorActionPreference = "Stop"

$WinInstall = $PSScriptRoot
$Root = Split-Path -Parent $WinInstall
$DistDir = Join-Path $WinInstall "dist"
$SetupOutput = Join-Path $DistDir "Rugdraiger_Dowloader_Music.exe"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$VenvPip = Join-Path $Root ".venv\Scripts\pip.exe"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "  RUGDRAIGER DOWNLOADER - BUILD INSTALADOR WIN" -ForegroundColor Red

if (-not (Test-Path $VenvPython)) {
    Write-Step "Creando entorno virtual..."
    Set-Location $Root
    python -m venv .venv
}

Write-Step "Instalando dependencias de build..."
& $VenvPip install -q -r (Join-Path $Root "requirements.txt")
& $VenvPip install -q pyinstaller pillow

$BinDir = Join-Path $Root "bin"
$Ytdlp = Join-Path $BinDir "yt-dlp.exe"
if (-not (Test-Path $Ytdlp)) {
    Write-Step "Descargando yt-dlp..."
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    Invoke-WebRequest -Uri "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" -OutFile $Ytdlp -UseBasicParsing
}

$AssetsDir = Join-Path $WinInstall "assets"
New-Item -ItemType Directory -Force -Path $AssetsDir | Out-Null
$IconPng = Join-Path $AssetsDir "app-icon.png"
$IconIco = Join-Path $AssetsDir "app-icon.ico"
if (-not (Test-Path $IconPng)) {
    Write-Step "Descargando icono Rugdraiger..."
    Invoke-WebRequest -Uri "https://rugdraiger.github.io/rugdraiger_play/icons/app-icon.png" -OutFile $IconPng -UseBasicParsing
}
if (-not (Test-Path $IconIco)) {
    Write-Step "Generando app-icon.ico..."
    & $VenvPython (Join-Path $WinInstall "make_icon.py")
}
$RootAssets = Join-Path $Root "assets"
New-Item -ItemType Directory -Force -Path $RootAssets | Out-Null
Copy-Item $IconPng (Join-Path $RootAssets "app-icon.png") -Force
Copy-Item $IconIco (Join-Path $RootAssets "app-icon.ico") -Force

Write-Step "Compilando aplicacion con PyInstaller..."
Set-Location $Root
& $VenvPython -m PyInstaller (Join-Path $WinInstall "Rugdraiger_Dowloader_Music.spec") --distpath (Join-Path $WinInstall "build") --workpath (Join-Path $WinInstall "pyinstaller-work") --noconfirm --clean

$AppExe = Join-Path $WinInstall "build\Rugdraiger_Dowloader_Music\Rugdraiger_Dowloader_Music.exe"
if (-not (Test-Path $AppExe)) {
    throw "No se genero el ejecutable de la aplicacion."
}

Write-Step "Creando payload.zip..."
& $VenvPython (Join-Path $WinInstall "make_payload.py")

Write-Step "Compilando instalador Rugdraiger_Dowloader_Music.exe..."
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
Set-Location $WinInstall
& $VenvPython -m PyInstaller (Join-Path $WinInstall "installer.spec") --distpath $DistDir --workpath (Join-Path $WinInstall "pyinstaller-work-installer") --noconfirm --clean

if (-not (Test-Path $SetupOutput)) {
    throw "No se genero el instalador en $SetupOutput"
}

$sizeMb = [math]::Round((Get-Item $SetupOutput).Length / 1048576, 1)
Write-Host ""
Write-Host "  LISTO." -ForegroundColor Green
Write-Host "  Instalador: $SetupOutput" -ForegroundColor Green
Write-Host "  Tamano: $sizeMb MB" -ForegroundColor Green
Write-Host ""
