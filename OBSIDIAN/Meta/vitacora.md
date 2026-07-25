# Vitácora — Segundo Cerebro

Registro cronológico del proyecto **PROYECTO BOMBERO** (Rugdraiger Downloader Music).

---

## 2026-05-29 | INICIO | Creación del proyecto

- Creado `regla_de_oro.txt` con reglas de trabajo acordadas.
- Iniciado desarrollo de aplicación Windows para descargar música de YouTube Music.
- Motor elegido: **yt-dlp** (estándar de la industria, mantenido en GitHub).
- Diseño visual alineado con Rugdraiger Play: fondo negro carbón (#000/#131313), contorno rojo intenso (#FF0000), tipografías Montserrat + Inter.
- Estrategia de calidad: descarga nativa M4A/Opus sin re-codificar; cookies del navegador para Premium (256 kbps AAC); `--extractor-args youtube:formats=missing_pot` para YouTube Music Premium.

## 2026-05-29 | BUILD | Aplicación funcional v1.0

- Creada GUI CustomTkinter con tema Rugdraiger Play (negro carbón + borde rojo).
- Motor yt-dlp 2026.03.17 integrado en `bin/`.
- Node.js detectado; ffmpeg pendiente de instalar en el sistema del usuario.
- Scripts `setup.bat` y `run.bat` listos para Windows.

## 2026-05-29 | INSTALLER | Rugdraiger_Dowloader_Music.exe

- Creada carpeta `win install/` con pipeline PyInstaller.
- Generado instalador `win install/dist/Rugdraiger_Dowloader_Music.exe` (~44 MB).
- Incluye app + yt-dlp; interfaz de instalacion estilo Rugdraiger.

## 2026-05-29 | FIX | Error yt-dlp codigo 1 al descargar

- Causa: ffmpeg no instalado; postproceso (caratula/metadatos/remux) fallaba.
- Fix: sin ffmpeg descarga audio nativo; con ffmpeg activa todas las opciones.
- Anadido --js-runtimes node cuando Node.js esta disponible.
- Mensajes de error mas claros en el dialogo.

## 2026-05-29 | GUARDADO | Persistencia del proyecto

- Usuario pidio "guarda todo".
- Inicializado repositorio git local con commit del estado completo del proyecto.

## 2026-07-25 | TEST | Verificacion playlist completa

- Verificado descarga de playlists (youtube.com y music.youtube.com).
- Mejoras: --yes-playlist, nombres 01 - Artista - Titulo, progreso por cancion.
- Pruebas OK: tests/test_playlist_download.py (3 escenarios).
- Instalador recompilado.

## 2026-07-25 | PACK | ffmpeg y Node.js incluidos en el instalador

- Script scripts/fetch_runtime_deps.py descarga ffmpeg + Node LTS a bin/.
- Se empaquetan con PyInstaller; el usuario no necesita winget ni pasos extra.
- setup.bat y build-installer.ps1 ejecutan el script automaticamente.

---
