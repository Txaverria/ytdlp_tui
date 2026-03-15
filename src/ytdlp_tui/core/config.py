from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from ytdlp_tui.core.paths import config_file_path
from ytdlp_tui.core.platform import get_default_downloads_dir


@dataclass(slots=True)
class AppConfig:
    download_dir: str
    output_format: str
    quality: str
    theme: str | None = None


def default_config() -> AppConfig:
    return AppConfig(
        download_dir=get_default_downloads_dir(),
        output_format="mp4",
        quality="high",
        theme=None,
    )


def load_config() -> AppConfig:
    path = config_file_path()
    if not path.exists():
        return default_config()

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    defaults = default_config()
    return AppConfig(
        download_dir=data.get("download_dir", defaults.download_dir),
        output_format=data.get("output_format", defaults.output_format),
        quality=data.get("quality", defaults.quality),
        theme=data.get("theme", defaults.theme),
    )


def save_config(config: AppConfig) -> None:
    path = config_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")


__all__ = ["AppConfig", "default_config", "load_config", "save_config", "get_default_downloads_dir"]
