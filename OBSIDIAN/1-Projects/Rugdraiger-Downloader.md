# Rugdraiger Downloader Music

## Objetivo

Aplicación de escritorio Windows para descargar audio de YouTube Music en la mejor calidad posible usando yt-dlp.

## Stack

- Python 3.13 + CustomTkinter (GUI)
- yt-dlp (binario embebido/descargable)
- ffmpeg (requerido para metadatos y carátulas)

## Calidad de audio

| Cuenta | Codec típico | Bitrate |
|--------|--------------|---------|
| Gratuita | Opus | ~128 kbps |
| Premium | AAC | ~256 kbps |

Formato recomendado: **M4A** (sin conversión) o **Opus** nativo.
