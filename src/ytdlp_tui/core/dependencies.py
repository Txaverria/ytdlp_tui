from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ytdlp_tui.core.models import DependencyStatus
from ytdlp_tui.core.paths import managed_bin_dir
from ytdlp_tui.core.platform import current_platform


def managed_ytdlp_path() -> Path:
    suffix = ".exe" if current_platform() == "windows" else ""
    return managed_bin_dir() / f"yt-dlp{suffix}"


def managed_ffmpeg_path() -> Path:
    suffix = ".exe" if current_platform() == "windows" else ""
    return managed_bin_dir() / f"ffmpeg{suffix}"


def detect_ytdlp() -> DependencyStatus:
    system = current_platform()
    system_path = shutil.which("yt-dlp")
    managed_path = managed_ytdlp_path()

    if system in {"linux", "macos"} and system_path:
        return DependencyStatus(
            name="yt-dlp",
            available=True,
            source="system",
            version=_read_version([system_path, "--version"]),
            path=system_path,
        )

    if managed_path.exists():
        return DependencyStatus(
            name="yt-dlp",
            available=True,
            source="managed",
            version=_read_version([str(managed_path), "--version"]),
            path=str(managed_path),
        )

    if system_path:
        return DependencyStatus(
            name="yt-dlp",
            available=True,
            source="system",
            version=_read_version([system_path, "--version"]),
            path=system_path,
        )

    return DependencyStatus(
        name="yt-dlp",
        available=False,
        source="missing",
        message=_missing_message("yt-dlp"),
    )


def detect_ffmpeg() -> DependencyStatus:
    system = current_platform()
    system_path = shutil.which("ffmpeg")
    managed_path = managed_ffmpeg_path()

    if system in {"linux", "macos"} and system_path:
        return DependencyStatus(
            name="ffmpeg",
            available=True,
            source="system",
            version=_read_ffmpeg_version(system_path),
            path=system_path,
        )

    if managed_path.exists():
        return DependencyStatus(
            name="ffmpeg",
            available=True,
            source="managed",
            version=_read_ffmpeg_version(str(managed_path)),
            path=str(managed_path),
        )

    if system_path:
        return DependencyStatus(
            name="ffmpeg",
            available=True,
            source="system",
            version=_read_ffmpeg_version(system_path),
            path=system_path,
        )

    return DependencyStatus(
        name="ffmpeg",
        available=False,
        source="missing",
        message=_missing_message("ffmpeg"),
    )


def _read_version(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError:
        return None

    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0].strip() if output else None


def _read_ffmpeg_version(executable: str) -> str | None:
    version = _read_version([executable, "-version"])
    if not version:
        return None

    parts = version.split()
    if len(parts) >= 3 and parts[0].lower() == "ffmpeg" and parts[1].lower() == "version":
        return parts[2]
    return version


def _missing_message(name: str) -> str:
    system = current_platform()
    if system == "windows":
        return f"{name} is not installed yet. Windows will use a managed download flow."
    return f"{name} was not found on this system. Install it or use managed downloads later."
