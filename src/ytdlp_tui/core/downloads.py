from __future__ import annotations

from ytdlp_tui.core.dependencies import detect_ffmpeg, detect_ytdlp
from ytdlp_tui.core.models import DownloadRequest


def validate_download_request(request: DownloadRequest) -> list[str]:
    errors: list[str] = []

    if not request.source.strip():
        errors.append("Enter a URL or search term.")

    ytdlp = detect_ytdlp()
    if not ytdlp.available:
        errors.append(ytdlp.message or "yt-dlp is not available.")

    if request.mode in {"audio", "video"}:
        ffmpeg = detect_ffmpeg()
        if not ffmpeg.available:
            errors.append(ffmpeg.message or "ffmpeg is not available.")

    return errors
