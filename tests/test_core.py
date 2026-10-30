"""Pruebas unitarias del núcleo multiplataforma."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import AppSettings
from app.core.dependencies import js_runtime_args
from app.core.downloader import DownloadJob, YtDlpDownloader
from app.core.url_utils import is_playlist_url, is_supported_url
from app.core.validators import normalize_playlist_items, validate_playlist_items


class UrlTests(unittest.TestCase):
    def test_supported_youtube_hosts(self) -> None:
        self.assertTrue(is_supported_url("https://music.youtube.com/watch?v=abc"))
        self.assertTrue(is_supported_url("https://youtu.be/abc"))
        self.assertFalse(is_supported_url("https://youtube.com.example.org/watch?v=abc"))
        self.assertFalse(is_supported_url("file:///tmp/video"))

    def test_playlist_detection(self) -> None:
        self.assertTrue(is_playlist_url("https://youtube.com/playlist?list=PL123"))
        self.assertTrue(is_playlist_url("https://youtu.be/abc?list=PL123"))
        self.assertFalse(is_playlist_url("https://youtu.be/abc"))


class ValidatorTests(unittest.TestCase):
    def test_playlist_items_are_normalized(self) -> None:
        self.assertEqual(normalize_playlist_items(" 1 – 5, 8 "), "1-5,8")
        self.assertEqual(validate_playlist_items("1-5,8"), (True, ""))

    def test_invalid_playlist_items_are_rejected(self) -> None:
        valid, _ = validate_playlist_items("1; rm -rf")
        self.assertFalse(valid)
        valid, _ = validate_playlist_items("1--5")
        self.assertFalse(valid)


class DependencyTests(unittest.TestCase):
    @patch("app.core.dependencies.find_js_runtime")
    def test_runtime_argument_contains_absolute_binary(self, find_runtime) -> None:
        find_runtime.return_value = ("deno", Path("/opt/homebrew/bin/deno"))
        self.assertEqual(
            js_runtime_args(),
            ["--js-runtimes", "deno:/opt/homebrew/bin/deno"],
        )


class DownloaderCommandTests(unittest.TestCase):
    def test_m4a_command_is_cross_platform_and_produces_final_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = AppSettings(output_dir=directory, audio_format="m4a")
            job = DownloadJob("https://music.youtube.com/watch?v=abc", settings)
            with (
                patch("app.core.downloader.ffmpeg_available", return_value=True),
                patch("app.core.downloader.ffmpeg_location_args", return_value=[]),
                patch("app.core.downloader.js_runtime_args", return_value=[]),
            ):
                command, _ = YtDlpDownloader()._build_command(job, Path("/tmp/yt-dlp"))

        self.assertIn("--audio-format", command)
        self.assertIn("m4a", command)
        self.assertIn("after_move:__RUGDRAIGER_FILE__:%(filepath)s", command)
        self.assertNotIn("--extractor-args", command)

    def test_premium_command_uses_cookie_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cookies = Path(directory) / "cookies.txt"
            cookies.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
            settings = AppSettings(
                output_dir=directory,
                use_cookies=True,
                cookies_file=str(cookies),
            )
            job = DownloadJob("https://music.youtube.com/watch?v=abc", settings)
            with (
                patch("app.core.downloader.ffmpeg_available", return_value=True),
                patch("app.core.downloader.ffmpeg_location_args", return_value=[]),
                patch("app.core.downloader.js_runtime_args", return_value=[]),
            ):
                command, _ = YtDlpDownloader()._build_command(job, Path("/tmp/yt-dlp"))

        self.assertIn("--cookies", command)
        self.assertIn(str(cookies), command)
        self.assertIn("--extractor-args", command)


if __name__ == "__main__":
    unittest.main()
