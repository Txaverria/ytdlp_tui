from __future__ import annotations

import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Callable

from ytdlp_tui.core.dependencies import detect_ffmpeg, detect_ytdlp
from ytdlp_tui.core.models import DownloadRequest, DownloadResult


def run_download(
    request: DownloadRequest,
    cancel_event: threading.Event | None = None,
    output_callback: Callable[[str], None] | None = None,
) -> DownloadResult:
    ytdlp = detect_ytdlp()
    if not ytdlp.available or not ytdlp.path:
        return DownloadResult(
            success=False,
            output=[],
            downloaded_files=[],
            summary="yt-dlp is unavailable.",
            error=ytdlp.message or "yt-dlp is not available.",
        )

    ffmpeg = detect_ffmpeg()
    args = _build_args(request, ytdlp.path, ffmpeg.path if ffmpeg.available else None)
    output_lines: list[str] = []
    Path(request.download_dir).mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(prefix="ytdlp-tui-", suffix=".txt", delete=False) as tmp:
        print_file = Path(tmp.name)

    args.extend(["--print-to-file", "after_move:filepath", str(print_file)])

    try:
        process = subprocess.Popen(
            args,
            cwd=request.download_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except OSError as exc:
        return DownloadResult(
            success=False,
            output=[],
            downloaded_files=[],
            summary="The download process could not be started.",
            error=str(exc),
        )

    cancelled = False
    assert process.stdout is not None
    for raw_line in process.stdout:
        line = raw_line.strip()
        if line:
            output_lines.append(line)
            if output_callback is not None:
                output_callback(line)

        if cancel_event and cancel_event.is_set():
            cancelled = True
            process.terminate()
            break

    try:
        process.wait(timeout=3 if cancelled else None)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()

    downloaded_files = _read_downloaded_files(print_file)
    success = process.returncode == 0 and not cancelled
    error = None if success else f"yt-dlp exited with code {process.returncode}"
    progress_line = _last_matching_line(output_lines, "[download]")
    summary = _build_summary(success, output_lines, downloaded_files, error, cancelled)

    return DownloadResult(
        success=success,
        output=output_lines,
        downloaded_files=downloaded_files,
        summary=summary,
        progress_line=progress_line,
        cancelled=cancelled,
        error=error,
    )


def _build_args(request: DownloadRequest, ytdlp_path: str, ffmpeg_path: str | None) -> list[str]:
    output_template = str(Path(request.download_dir) / "%(title)s.%(ext)s")
    args = [ytdlp_path, "-o", output_template]

    if ffmpeg_path:
        args.extend(["--ffmpeg-location", str(Path(ffmpeg_path).parent)])

    quality = request.quality
    output_format = request.output_format

    if output_format == "mp3":
        args.extend(["-f", _audio_selector_for_quality(quality)])
        args.extend(["-x", "--audio-format", "mp3", "--audio-quality", _audio_quality_for(quality, high="0", medium="4", low="7")])
    elif output_format == "m4a":
        args.extend(["-f", _audio_selector_for_quality(quality)])
        args.extend(["-x", "--audio-format", "m4a", "--audio-quality", _audio_quality_for(quality, high="0", medium="4", low="7")])
    elif output_format == "ogg":
        args.extend(["-f", _audio_selector_for_quality(quality)])
        args.extend(["-x", "--audio-format", "vorbis", "--audio-quality", _audio_quality_for(quality, high="4", medium="6", low="8")])
    elif output_format == "mp4":
        if quality == "high":
            args.extend(["-f", "bestvideo*+bestaudio/best"])
        elif quality == "medium":
            args.extend(["-f", "bestvideo*[height<=720]+bestaudio/best[height<=720]/best[height<=720]/best"])
        else:
            args.extend(["-f", "worstvideo*+worstaudio/worst"])
        args.extend(["--remux-video", "mp4"])
    elif output_format == "webm":
        if quality == "high":
            args.extend(["-f", "bestvideo*[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best"])
        elif quality == "medium":
            args.extend(["-f", "bestvideo*[ext=webm][height<=720]+bestaudio[ext=webm]/best[ext=webm][height<=720]/best[height<=720]/best"])
        else:
            args.extend(["-f", "worstvideo*[ext=webm]+worstaudio[ext=webm]/worst[ext=webm]/worst"])

    args.extend(request.sources)
    return args


def _audio_selector_for_quality(quality: str) -> str:
    if quality == "low":
        return "worstaudio/bestaudio/best"
    return "bestaudio/best"


def _audio_quality_for(quality: str, *, high: str, medium: str, low: str) -> str:
    if quality == "high":
        return high
    if quality == "medium":
        return medium
    return low


def _read_downloaded_files(path: Path) -> list[str]:
    try:
        if not path.exists():
            return []
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    finally:
        path.unlink(missing_ok=True)


def _last_matching_line(lines: list[str], prefix: str) -> str | None:
    for line in reversed(lines):
        if line.startswith(prefix):
            return line
    return None


def _build_summary(
    success: bool,
    output_lines: list[str],
    downloaded_files: list[str],
    error: str | None,
    cancelled: bool,
) -> str:
    if cancelled:
        return "Download cancelled."

    if success:
        if downloaded_files:
            file_count = len(downloaded_files)
            file_label = "file" if file_count == 1 else "files"
            return f"[OK] Finished successfully. {file_count} {file_label} ready."

        destination_line = _last_matching_line(output_lines, "[Merger] Merging formats into ")
        if destination_line:
            return "[OK] Finished successfully after merging formats."

        destination_line = _last_matching_line(output_lines, "[ExtractAudio] Destination: ")
        if destination_line:
            return "[OK] Finished successfully after audio extraction."

        destination_line = _last_matching_line(output_lines, "[download] Destination: ")
        if destination_line:
            return "[OK] Finished successfully."

        return "[OK] Finished successfully."

    if error:
        yt_error = _build_youtube_helpful_error(output_lines)
        if yt_error:
            return yt_error
        return error

    error_line = _last_matching_line(output_lines, "ERROR:")
    if error_line:
        yt_error = _build_youtube_helpful_error(output_lines)
        if yt_error:
            return yt_error
        return error_line

    return "Download failed."


def _build_youtube_helpful_error(output_lines: list[str]) -> str | None:
    has_js_runtime_warning = any(
        "No supported JavaScript runtime could be found" in line for line in output_lines
    )
    has_bot_confirmation_error = any(
        "Sign in to confirm you’re not a bot" in line for line in output_lines
    )

    if has_js_runtime_warning and has_bot_confirmation_error:
        return (
            "YouTube blocked this request. Install Deno and try again. "
            "If it still fails, use browser cookies with yt-dlp."
        )

    if has_js_runtime_warning:
        return "YouTube may require a JavaScript runtime. Install Deno and try again."

    if has_bot_confirmation_error:
        return "YouTube blocked this request. Try again with browser cookies in yt-dlp."

    return None
