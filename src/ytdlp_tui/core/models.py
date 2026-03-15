from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DownloadRequest:
    sources: list[str]
    output_format: str
    quality: str
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
    summary: str | None = None
    progress_line: str | None = None
    cancelled: bool = False
    error: str | None = None
