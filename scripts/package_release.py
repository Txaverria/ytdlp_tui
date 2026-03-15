from __future__ import annotations

import platform
import shutil
import subprocess
import tarfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
ENTRYPOINT = ROOT / "src" / "ytdlp_tui" / "__main__.py"
APP_NAME = "ytdlp-tui"
ICON_PATH = ROOT / "assets" / "icon.ico"


def main() -> None:
    system = normalized_system()
    pyinstaller_cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--console",
        "--name",
        APP_NAME,
        "--paths",
        str(ROOT / "src"),
        str(ENTRYPOINT),
    ]
    if ICON_PATH.exists():
        pyinstaller_cmd.extend(["--icon", str(ICON_PATH)])
    subprocess.run(pyinstaller_cmd, check=True, cwd=ROOT)

    bundle_dir = DIST_DIR / bundle_name(system)
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    source_dir = DIST_DIR / APP_NAME
    shutil.copytree(source_dir, bundle_dir / APP_NAME, dirs_exist_ok=True)
    shutil.copy2(ROOT / "README.md", bundle_dir / "README.md")

    archive_path = create_archive(bundle_dir, system)
    print(archive_path)


def normalized_system() -> str:
    system = platform.system().lower()
    if system.startswith("darwin"):
        return "macos"
    if system.startswith("windows"):
        return "windows"
    return "linux"


def bundle_name(system: str) -> str:
    machine = platform.machine().lower()
    return f"{APP_NAME}-{system}-{machine}"


def create_archive(bundle_dir: Path, system: str) -> Path:
    if system == "windows":
        archive_path = DIST_DIR / f"{bundle_dir.name}.zip"
        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
            for path in bundle_dir.rglob("*"):
                archive.write(path, path.relative_to(bundle_dir.parent))
        return archive_path

    archive_path = DIST_DIR / f"{bundle_dir.name}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(bundle_dir, arcname=bundle_dir.name)
    return archive_path


if __name__ == "__main__":
    main()
