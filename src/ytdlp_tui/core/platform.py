from __future__ import annotations

import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DependencyPolicy:
    ytdlp: str
    ffmpeg: str


def current_platform() -> str:
    system = platform.system().lower()
    if system.startswith("darwin"):
        return "macos"
    if system.startswith("windows"):
        return "windows"
    return "linux"


def dependency_policy_for_current_platform() -> DependencyPolicy:
    system = current_platform()
    if system == "windows":
        return DependencyPolicy(
            ytdlp="managed download by default",
            ffmpeg="managed download by default",
        )
    return DependencyPolicy(
        ytdlp="prefer system install",
        ffmpeg="prefer system install",
    )


def get_default_downloads_dir() -> str:
    return str(Path.home() / "Downloads")
