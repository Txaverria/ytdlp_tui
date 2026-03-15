from __future__ import annotations

import re

from ytdlp_tui.core.dependencies import detect_ffmpeg, detect_ytdlp
from ytdlp_tui.core.models import DownloadRequest


def validate_download_request(request: DownloadRequest) -> list[str]:
    errors: list[str] = []

    if not request.sources:
        errors.append("Enter at least one URL or search term.")

    ytdlp = detect_ytdlp()
    if not ytdlp.available:
        errors.append(ytdlp.message or "yt-dlp is not available.")

    if request.output_format in {"mp3", "ogg", "mp4"}:
        ffmpeg = detect_ffmpeg()
        if not ffmpeg.available:
            errors.append(ffmpeg.message or "ffmpeg is not available.")

    return errors


def parse_sources(raw_input: str) -> list[str]:
    normalized = re.sub(r"[,\n;]+", "\n", raw_input.strip())
    if not normalized:
        return []

    chunks = [chunk.strip() for chunk in normalized.splitlines() if chunk.strip()]
    sources: list[str] = []

    for chunk in chunks:
        whitespace_parts = chunk.split()
        if len(whitespace_parts) > 1 and all(_looks_like_url_or_path(part) for part in whitespace_parts):
            sources.extend(whitespace_parts)
        else:
            sources.append(chunk)

    return sources


def _looks_like_url_or_path(value: str) -> bool:
    return "://" in value or value.startswith(("www.", "/", "./", "../", "~"))
