Genera el instalador Windows **`Rugdraiger_Dowloader_Music.exe`**.

## Requisitos

- Python 3.11+ con entorno del proyecto (`.venv` en la raíz)
- Conexión a Internet (descarga yt-dlp e icono si hace falta)

## Compilar

```bat
build-installer.bat
```

## Salida

```
win install/dist/Rugdraiger_Dowloader_Music.exe   (~45 MB)
```

El instalador incluye:

- Interfaz de instalacion (negro carbón + rojo Rugdraiger)
- Aplicacion completa + yt-dlp embebido
- Acceso directo en menu Inicio
- Opcion de acceso directo en escritorio
- Script `uninstall.bat` en la carpeta de instalacion
- Configuracion en `%APPDATA%\RugdraigerDownloader\config`

## Instalacion por defecto

`%LOCALAPPDATA%\Rugdraiger Downloader Music`

## Nota

Para caratulas y metadatos, instala **ffmpeg** en el PATH: `winget install Gyan.FFmpeg`
