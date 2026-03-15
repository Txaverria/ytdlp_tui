from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from ytdlp_tui import __version__


LATEST_RELEASE_API = "https://api.github.com/repos/Txaverria/ytdlp_tui/releases/latest"
LATEST_RELEASE_PAGE = "https://github.com/Txaverria/ytdlp_tui/releases/latest"


@dataclass(slots=True)
class ReleaseInfo:
    current_version: str
    latest_version: str | None = None
    release_url: str = LATEST_RELEASE_PAGE
    update_available: bool = False
    error: str | None = None


def get_current_version() -> str:
    return __version__


def fetch_latest_release_info(timeout: float = 5.0) -> ReleaseInfo:
    info = ReleaseInfo(current_version=get_current_version())
    request = Request(
        LATEST_RELEASE_API,
        headers={
            "User-Agent": "ytdlp-tui",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except URLError as exc:
        info.error = str(exc.reason)
        return info
    except Exception as exc:
        info.error = str(exc)
        return info

    latest_tag = str(payload.get("tag_name") or "").strip()
    latest_version = latest_tag[1:] if latest_tag.startswith("v") else latest_tag
    if latest_version:
        info.latest_version = latest_version
        info.update_available = _version_key(latest_version) > _version_key(info.current_version)
    html_url = payload.get("html_url")
    if isinstance(html_url, str) and html_url:
        info.release_url = html_url
    return info


def _version_key(version: str) -> tuple[int, ...]:
    parts = version.split(".")
    key: list[int] = []
    for part in parts:
        digits = "".join(ch for ch in part if ch.isdigit())
        key.append(int(digits) if digits else 0)
    return tuple(key)
