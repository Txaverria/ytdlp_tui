from __future__ import annotations

import shutil
import stat
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from ytdlp_tui.core.models import DependencyStatus
from ytdlp_tui.core.paths import managed_bin_dir
from ytdlp_tui.core.platform import current_platform


YTDLP_RELEASE_BASE = "https://github.com/yt-dlp/yt-dlp/releases/latest/download"


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


def install_managed_ytdlp() -> DependencyStatus:
    destination = managed_ytdlp_path()
    destination.parent.mkdir(parents=True, exist_ok=True)

    asset_name = _ytdlp_asset_name()
    url = f"{YTDLP_RELEASE_BASE}/{asset_name}"

    with tempfile.NamedTemporaryFile(prefix="ytdlp-tui-", suffix=destination.suffix, delete=False) as tmp:
        temp_path = Path(tmp.name)

    try:
        with urllib.request.urlopen(url) as response, temp_path.open("wb") as output:
            shutil.copyfileobj(response, output)

        _make_executable(temp_path)
        temp_path.replace(destination)
    finally:
        temp_path.unlink(missing_ok=True)

    return detect_ytdlp()


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


def _ytdlp_asset_name() -> str:
    system = current_platform()
    if system == "windows":
        return "yt-dlp.exe"
    if system == "macos":
        return "yt-dlp_macos"
    return "yt-dlp"


def _make_executable(path: Path) -> None:
    if current_platform() == "windows":
        return
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
