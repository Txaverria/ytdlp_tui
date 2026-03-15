import platform
from pathlib import Path


APP_DIR_NAME = "ytdlp-tui"


def config_dir() -> Path:
    system = platform.system().lower()
    home = Path.home()

    if system.startswith("windows"):
        appdata = home / "AppData" / "Roaming"
        return appdata / APP_DIR_NAME

    if system.startswith("darwin"):
        return home / "Library" / "Application Support" / APP_DIR_NAME

    return home / ".config" / APP_DIR_NAME


def config_file_path() -> Path:
    return config_dir() / "config.json"


def data_dir() -> Path:
    system = platform.system().lower()
    home = Path.home()

    if system.startswith("windows"):
        local_appdata = home / "AppData" / "Local"
        return local_appdata / APP_DIR_NAME

    if system.startswith("darwin"):
        return home / "Library" / "Application Support" / APP_DIR_NAME

    return home / ".local" / "share" / APP_DIR_NAME


def managed_bin_dir() -> Path:
    return data_dir() / "bin"
