from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from ytdlp_tui.core.dependencies import detect_ffmpeg, detect_ytdlp
from ytdlp_tui.core.models import DownloadRequest, DownloadResult


def run_download(request: DownloadRequest) -> DownloadResult:
    ytdlp = detect_ytdlp()
    if not ytdlp.available or not ytdlp.path:
        return DownloadResult(
            success=False,
            output=[],
            downloaded_files=[],
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
        completed = subprocess.run(
            args,
            cwd=request.download_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return DownloadResult(
            success=False,
            output=[],
            downloaded_files=[],
            error=str(exc),
        )

    if completed.stdout:
        output_lines.extend(line for line in completed.stdout.splitlines() if line.strip())
    if completed.stderr:
        output_lines.extend(line for line in completed.stderr.splitlines() if line.strip())

    downloaded_files = _read_downloaded_files(print_file)
    success = completed.returncode == 0
    error = None if success else f"yt-dlp exited with code {completed.returncode}"

    return DownloadResult(
        success=success,
        output=output_lines,
        downloaded_files=downloaded_files,
        error=error,
    )


def _build_args(request: DownloadRequest, ytdlp_path: str, ffmpeg_path: str | None) -> list[str]:
    output_template = str(Path(request.download_dir) / "%(title)s.%(ext)s")
    args = [ytdlp_path, "-o", output_template]

    if ffmpeg_path:
        args.extend(["--ffmpeg-location", str(Path(ffmpeg_path).parent)])

    if request.mode == "audio":
        args.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
    elif request.mode == "video":
        args.extend(["--remux-video", "mp4"])

    args.append(request.source)
    return args


def _read_downloaded_files(path: Path) -> list[str]:
    try:
        if not path.exists():
            return []
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    finally:
        path.unlink(missing_ok=True)
