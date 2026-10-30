# Rugdraiger Downloader Music

Aplicación de escritorio para descargar audio de YouTube y YouTube Music mediante
[yt-dlp](https://github.com/yt-dlp/yt-dlp). Compatible con macOS Apple Silicon
(M1, M2, M3 y M4) y Windows 10/11.

> Descarga únicamente contenido propio, con licencia compatible o para el cual
> tengas autorización. Respeta los términos del servicio y la legislación local.

## macOS Apple Silicon — instalación recomendada

Requiere macOS, conexión a Internet y [Homebrew](https://brew.sh). Desde Finder,
haz doble clic en `setup_macos.command`; desde Terminal:

```zsh
./setup_macos.command
./run_macos.command
```

El instalador:

- usa Python 3.13 arm64 y Tkinter nativo;
- instala FFmpeg y Deno mediante Homebrew cuando faltan;
- crea un entorno aislado en `.venv`;
- obtiene el ejecutable universal oficial de yt-dlp;
- ejecuta las pruebas antes de finalizar.

Los audios se guardan por defecto en `~/Music/Rugdraiger Downloads`. La
configuración de una app empaquetada se guarda en
`~/Library/Application Support/RugdraigerDownloader`.

Si Gatekeeper impide abrir un `.command`, haz clic secundario sobre él, selecciona
**Abrir** y confirma una sola vez.

## Crear la aplicación `.app` para el M4

```zsh
./build_macos.command
open "dist/Rugdraiger Downloader.app"
```

La compilación es nativa `arm64`, genera una aplicación sin consola y aplica una
firma local ad hoc. Esa firma sirve para usarla en el mismo Mac. Distribuirla a
otros equipos sin advertencias de Gatekeeper requiere un certificado Apple
Developer ID y notarización.

## Windows

```bat
setup.bat
run.bat
```

El instalador de Windows continúa disponible en `win install/`. Los cambios del
núcleo son multiplataforma y mantienen los ejecutables `.exe` en Windows.

## Uso

1. Pega una URL de canción, álbum o playlist de YouTube Music/YouTube.
2. Selecciona `m4a`, `opus`, `mp3` o `best`.
3. Para una playlist completa, deja **Ítems playlist** vacío; también acepta
   rangos como `1-10` o listas como `1,3,7`.
4. Opcionalmente activa cookies para usar tu sesión de YouTube Music.
5. Pulsa **DESCARGAR**. Puedes cancelar el proceso o abrir la carpeta de destino
   desde la propia aplicación.

### Formatos

- `m4a`: prioriza AAC/M4A y evita recodificar cuando el origen ya es compatible.
- `opus`: prioriza Opus y conserva el flujo compatible.
- `mp3`: convierte explícitamente con FFmpeg; no mejora la calidad del origen.
- `best`: conserva el mejor audio nativo que ofrece yt-dlp.

La calidad realmente disponible depende de YouTube, la cuenta, la región y el
formato publicado. Un número de bitrate mayor no recupera información perdida.

## Cookies en macOS

- Inicia sesión en el navegador seleccionado.
- Si macOS solicita acceso al Llavero, concédelo a la aplicación.
- Si Chrome/Brave bloquea la base de cookies, ciérralo completamente con `⌘Q`.
- Firefox o un `cookies.txt` en formato Netscape suelen ser las opciones más
  fiables.
- No compartas ni versiones `cookies.txt`; permite acceso a tu sesión.

## Desarrollo y verificación

```zsh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/ruff check .
```

`tests/test_playlist_download.py` es una prueba de integración manual que accede
a YouTube y descarga archivos. Las pruebas unitarias normales no descargan audio.

## Arquitectura

```text
main.py                    entrada de la aplicación
app/config.py              preferencias persistentes
app/paths.py               rutas por plataforma y por bundle
app/core/dependencies.py   yt-dlp, FFmpeg y runtime JavaScript
app/core/downloader.py     construcción y supervisión de descargas
app/core/validators.py     validación de entradas
app/ui/app_window.py       interfaz CustomTkinter
macos/                     configuración PyInstaller arm64
tests/                     pruebas unitarias e integración manual
```

El ejecutable de yt-dlp se mantiene fuera del bundle empaquetado para poder
actualizarlo sin modificar la firma de la aplicación. La app detecta herramientas
en su directorio privado, en el bundle, en el `PATH` y en las ubicaciones estándar
de Homebrew para que también funcione al abrirla desde Finder.
