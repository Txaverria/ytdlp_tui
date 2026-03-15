from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DownloadRequest:
    source: str
    mode: str
    download_dir: str


@dataclass(slots=True)
class DependencyStatus:
    name: str
    available: bool
    source: str
    version: str | None = None
    path: str | None = None
    message: str | None = None


@dataclass(slots=True)
class DownloadResult:
    success: bool
    output: list[str]
    downloaded_files: list[str]
    error: str | None = None
