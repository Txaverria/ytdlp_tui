from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from ytdlp_tui import __version__


APP_NAME = "ytdlp-tui"
UPDATER_NAME = "ytdlp-tui-updater"
UNINSTALLER_NAME = "ytdlp-tui-uninstaller"
REPO = "Txaverria/ytdlp_tui"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPO}/releases/latest"
LATEST_RELEASE_PAGE = f"https://github.com/{REPO}/releases/latest"
WINDOWS_ASSET_NAME = "ytdlp-tui-windows-amd64.zip"


@dataclass(slots=True)
class InstallMetadata:
    app_name: str
    version: str
    install_dir: str
    start_menu_dir: str
    app_shortcut: str
    update_shortcut: str
    uninstall_shortcut: str


@dataclass(slots=True)
class ReleaseAsset:
    version: str
    url: str
    release_page: str


@dataclass(slots=True)
class InstallContext:
    install_dir: Path
    source: str
    metadata: InstallMetadata | None


def installer_state_dir() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "ytdlp-tui-installer"
    return Path.home() / "AppData" / "Local" / "ytdlp-tui-installer"


def metadata_path() -> Path:
    return installer_state_dir() / "install.json"


def load_metadata() -> InstallMetadata:
    path = metadata_path()
    if not path.exists():
        raise RuntimeError("Installation metadata was not found. Install the app first.")
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return InstallMetadata(
        app_name=str(data["app_name"]),
        version=str(data["version"]),
        install_dir=str(data["install_dir"]),
        start_menu_dir=str(data["start_menu_dir"]),
        app_shortcut=str(data["app_shortcut"]),
        update_shortcut=str(data["update_shortcut"]),
        uninstall_shortcut=str(data["uninstall_shortcut"]),
    )


def load_metadata_optional() -> InstallMetadata | None:
    try:
        return load_metadata()
    except Exception:
        return None


def save_metadata(metadata: InstallMetadata) -> None:
    path = metadata_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(metadata), indent=2), encoding="utf-8")


def current_version() -> str:
    return __version__


def updater_exe_name() -> str:
    return f"{UPDATER_NAME}.exe"


def uninstaller_exe_name() -> str:
    return f"{UNINSTALLER_NAME}.exe"


def app_exe_name() -> str:
    return f"{APP_NAME}.exe"


def app_dir_from_current_executable() -> Path | None:
    current = Path(sys.executable).resolve()
    if current.name.lower() in {app_exe_name().lower(), updater_exe_name().lower(), uninstaller_exe_name().lower()}:
        return current.parent
    return None


def assert_safe_app_dir(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == resolved.anchor:
        raise RuntimeError(f"Refusing to use a filesystem root as the install path: {resolved}")
    if resolved.name != APP_NAME:
        raise RuntimeError(
            f"Refusing to use an unexpected install path. Expected the final folder name to be '{APP_NAME}': {resolved}"
        )
    return resolved


def assert_safe_start_menu_dir(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == resolved.anchor:
        raise RuntimeError(f"Refusing to use a filesystem root as the Start Menu path: {resolved}")
    if resolved.name != APP_NAME:
        raise RuntimeError(f"Refusing to use an unexpected Start Menu folder: {resolved}")
    return resolved


def fetch_latest_windows_release() -> ReleaseAsset:
    request = Request(
        LATEST_RELEASE_API,
        headers={
            "User-Agent": f"{APP_NAME}-helper",
            "Accept": "application/vnd.github+json",
        },
    )
    with urlopen(request, timeout=10) as response:
        payload = json.load(response)
    assets = payload.get("assets") or []
    match = next((asset for asset in assets if asset.get("name") == WINDOWS_ASSET_NAME), None)
    if match is None:
        raise RuntimeError(f"Could not find release asset '{WINDOWS_ASSET_NAME}' in the latest GitHub release.")
    tag_name = str(payload.get("tag_name") or "").strip()
    if not tag_name:
        raise RuntimeError("Latest GitHub release is missing a tag name.")
    return ReleaseAsset(
        version=tag_name,
        url=str(match["browser_download_url"]),
        release_page=str(payload.get("html_url") or LATEST_RELEASE_PAGE),
    )


def infer_install_context(cli_install_dir: str | None = None) -> InstallContext:
    if cli_install_dir:
        return InstallContext(
            install_dir=assert_safe_app_dir(Path(cli_install_dir).expanduser()),
            source="command-line argument",
            metadata=load_metadata_optional(),
        )

    current_dir = app_dir_from_current_executable()
    if current_dir is not None:
        metadata = load_metadata_optional()
        return InstallContext(
            install_dir=assert_safe_app_dir(current_dir),
            source="current executable",
            metadata=metadata,
        )

    metadata = load_metadata()
    return InstallContext(
        install_dir=assert_safe_app_dir(Path(metadata.install_dir)),
        source="installer metadata",
        metadata=metadata,
    )


def ask_for_confirmation(action: str, inferred_path: Path, source: str, token: str) -> bool:
    print("")
    print(f"Inferred install path from {source}:")
    print(f"  {inferred_path}")
    print("")
    choice = input(f"Type {token} to {action} or CANCEL to stop\n> ").strip()
    return choice == token


def ensure_app_not_running() -> None:
    proc = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {app_exe_name()}"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if app_exe_name().lower() in output.lower():
        raise RuntimeError(f"{app_exe_name()} is still running. Close the app before continuing.")


def download_release_zip(url: str) -> tuple[Path, Path]:
    temp_root = Path(tempfile.mkdtemp(prefix=f"{APP_NAME}-helper-"))
    zip_path = temp_root / WINDOWS_ASSET_NAME
    extract_dir = temp_root / "extract"
    request = Request(url, headers={"User-Agent": f"{APP_NAME}-helper"})
    with urlopen(request, timeout=60) as response, zip_path.open("wb") as destination:
        shutil.copyfileobj(response, destination)
    shutil.unpack_archive(str(zip_path), str(extract_dir))
    return temp_root, extract_dir


def find_bundle_dir(extract_dir: Path) -> Path:
    exe_match = next(extract_dir.rglob(app_exe_name()), None)
    if exe_match is None:
        raise RuntimeError(f"Could not find {app_exe_name()} inside the downloaded archive.")
    return exe_match.parent


def replace_app_dir(source_dir: Path, install_dir: Path) -> None:
    backup_dir = install_dir.with_name(f"{install_dir.name}.old")
    if backup_dir.exists():
        shutil.rmtree(backup_dir, ignore_errors=False)

    if install_dir.exists():
        try:
            install_dir.rename(backup_dir)
        except OSError as exc:
            raise RuntimeError(
                "The install folder is in use. Close the app and any Explorer or terminal windows open in that folder, then try again."
            ) from exc

    try:
        shutil.copytree(source_dir, install_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=False)
    except Exception:
        if not install_dir.exists() and backup_dir.exists():
            backup_dir.rename(install_dir)
        raise


def pause() -> None:
    print("")
    input("Press Enter to close")
