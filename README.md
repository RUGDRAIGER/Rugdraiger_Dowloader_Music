# Rugdraiger Downloader Music

Aplicación de escritorio **Windows** para descargar música de [YouTube Music](https://music.youtube.com) en la mejor calidad posible, usando [yt-dlp](https://github.com/yt-dlp/yt-dlp).

Interfaz visual alineada con [Rugdraiger Play](https://rugdraiger.github.io/rugdraiger_play/): fondo negro carbón, contorno rojo intenso, tipografías Montserrat + Inter.

## Calidad de audio

| Cuenta | Codec | Bitrate |
|--------|-------|---------|
| Gratuita | Opus | ~128 kbps |
| Premium (con cookies) | AAC | ~256 kbps |

**Recomendación:** usa formato **M4A** para conservar el AAC nativo sin re-codificar. Evita MP3 320 kbps sobre un origen ya comprimido.

## Requisitos

- Windows 10/11
- Conexión a Internet (solo para descargar música)

**Incluido en el instalador** (no hace falta instalar nada más):
- yt-dlp, **ffmpeg**, **Node.js**

Para desarrollo local además necesitas Python 3.11+ y ejecutar `setup.bat` una vez.

## Instalación rápida

```bat
setup.bat
run.bat
```

## Uso

1. Pega un enlace de canción, álbum o playlist de YouTube Music.
2. Elige formato **m4a** (recomendado) u **opus**.
3. Si tienes **YouTube Music Premium**, activa *Usar cookies del navegador* y selecciona tu navegador (Firefox suele ser más fiable que Chrome).
4. Pulsa **DESCARGAR**.

Los archivos se guardan en `~/Music/Rugdraiger Downloads` por defecto.

## YouTube Music Premium — cookies

Para acceder al flujo AAC 256 kbps:

1. Inicia sesión en YouTube Music en el navegador elegido.
2. Activa la opción de cookies en la app.
3. Si obtienes errores de formato, usa Firefox o exporta cookies desde una ventana privada (ver [wiki yt-dlp PO Token](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)).

## Estructura del proyecto

```
├── regla_de_oro.txt      # Reglas de trabajo del proyecto
├── main.py               # Entrada de la aplicación
├── app/
│   ├── theme.py          # Colores y tipografías Rugdraiger
│   ├── config.py         # Configuración persistente
│   ├── core/
│   │   ├── downloader.py # Motor yt-dlp
│   │   └── dependencies.py
│   └── ui/
│       └── app_window.py # Interfaz gráfica
├── bin/                  # yt-dlp.exe (descargado por setup)
└── OBSIDIAN/             # Bitácora y notas del proyecto
```

## Referencias

- [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Extracción de audio (guía yt-dlp)](https://yt-dlp-yt-dlp.mintlify.app/guides/audio-extraction)
- [Rugdraiger Play — Design System](https://github.com/RUGDRAIGER/rugdraiger_play/blob/main/Fuentes/DESIGN.md)

## Aviso legal

Descarga solo contenido para el que tengas derechos o permiso. Respeta los términos de servicio de YouTube Music y las leyes de copyright de tu país.
