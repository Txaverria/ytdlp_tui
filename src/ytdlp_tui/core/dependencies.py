from __future__ import annotations

import shutil
import stat
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

from ytdlp_tui.core.models import DependencyStatus
from ytdlp_tui.core.paths import managed_bin_dir
from ytdlp_tui.core.platform import current_platform


YTDLP_RELEASE_BASE = "https://github.com/yt-dlp/yt-dlp/releases/latest/download"
WINDOWS_FFMPEG_ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


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
    system_probe_path = shutil.which("ffprobe")
    managed_path = managed_ffmpeg_path()
    managed_probe_path = managed_path.with_name("ffprobe.exe" if system == "windows" else "ffprobe")

    if system in {"linux", "macos"} and system_path and system_probe_path:
        return DependencyStatus(
            name="ffmpeg",
            available=True,
            source="system",
            version=_read_ffmpeg_version(system_path),
            path=system_path,
        )

    if managed_path.exists() and managed_probe_path.exists():
        return DependencyStatus(
            name="ffmpeg",
            available=True,
            source="managed",
            version=_read_ffmpeg_version(str(managed_path)),
            path=str(managed_path),
        )

    if system_path and system_probe_path:
        return DependencyStatus(
            name="ffmpeg",
            available=True,
            source="system",
            version=_read_ffmpeg_version(system_path),
            path=system_path,
        )

    if system_path and not system_probe_path:
        return DependencyStatus(
            name="ffmpeg",
            available=False,
            source="partial",
            message="ffmpeg was found, but ffprobe is missing.",
            path=system_path,
        )

    return DependencyStatus(
        name="ffmpeg",
        available=False,
        source="missing",
        message=_missing_message("ffmpeg"),
    )


def detect_deno() -> DependencyStatus:
    deno_path = shutil.which("deno")
    if deno_path:
        return DependencyStatus(
            name="deno",
            available=True,
            source="system",
            version=_read_version([deno_path, "--version"]),
            path=deno_path,
        )

    return DependencyStatus(
        name="deno",
        available=False,
        source="missing",
        message="Deno was not found on this system.",
    )


def install_managed_ytdlp(progress_callback: Callable[[str], None] | None = None) -> DependencyStatus:
    destination = managed_ytdlp_path()
    destination.parent.mkdir(parents=True, exist_ok=True)

    asset_name = _ytdlp_asset_name()
    url = f"{YTDLP_RELEASE_BASE}/{asset_name}"

    with tempfile.NamedTemporaryFile(prefix="ytdlp-tui-", suffix=destination.suffix, delete=False) as tmp:
        temp_path = Path(tmp.name)

    try:
        _download_to_path(url, temp_path, progress_callback, "yt-dlp")

        _notify(progress_callback, "Installing yt-dlp...")
        _make_executable(temp_path)
        temp_path.replace(destination)
    finally:
        temp_path.unlink(missing_ok=True)

    return detect_ytdlp()


def install_managed_ffmpeg(progress_callback: Callable[[str], None] | None = None) -> DependencyStatus:
    system = current_platform()
    if system != "windows":
        raise RuntimeError("Managed ffmpeg install is currently implemented for Windows only.")

    destination_dir = managed_bin_dir()
    destination_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(prefix="ytdlp-tui-ffmpeg-", suffix=".zip", delete=False) as tmp:
        archive_path = Path(tmp.name)

    extract_dir = archive_path.with_suffix("")

    try:
        _download_to_path(WINDOWS_FFMPEG_ZIP_URL, archive_path, progress_callback, "ffmpeg")

        _notify(progress_callback, "Extracting ffmpeg archive...")
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_dir)

        bin_dir = _find_ffmpeg_bin_dir(extract_dir)
        _notify(progress_callback, "Installing ffmpeg and ffprobe...")
        for tool_name in ("ffmpeg.exe", "ffprobe.exe"):
            source = bin_dir / tool_name
            if source.exists():
                shutil.copy2(source, destination_dir / tool_name)
    finally:
        archive_path.unlink(missing_ok=True)
        shutil.rmtree(extract_dir, ignore_errors=True)

    return detect_ffmpeg()


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


def _find_ffmpeg_bin_dir(root: Path) -> Path:
    for candidate in root.rglob("bin"):
        if (candidate / "ffmpeg.exe").exists():
            return candidate
    raise RuntimeError("Could not find ffmpeg binaries in the downloaded archive.")


def _download_to_path(
    url: str,
    destination: Path,
    progress_callback: Callable[[str], None] | None,
    label: str,
) -> None:
    _notify(progress_callback, f"Downloading {label}...")
    with urllib.request.urlopen(url) as response, destination.open("wb") as output:
        total = response.headers.get("Content-Length")
        total_bytes = int(total) if total and total.isdigit() else None
        downloaded = 0
        while True:
            chunk = response.read(1024 * 256)
            if not chunk:
                break
            output.write(chunk)
            downloaded += len(chunk)
            if total_bytes:
                percent = downloaded * 100 / total_bytes
                _notify(progress_callback, f"Downloading {label}... {percent:.0f}%")


def _notify(progress_callback: Callable[[str], None] | None, message: str) -> None:
    if progress_callback is not None:
        progress_callback(message)
