from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ytdlp_tui.core.windows_installer import (
    APP_NAME,
    assert_safe_app_dir,
    assert_safe_start_menu_dir,
    infer_install_context,
    pause,
    uninstaller_exe_name,
)


def run() -> None:
    parser = argparse.ArgumentParser(prog=uninstaller_exe_name())
    parser.add_argument("--relaunch", action="store_true")
    parser.add_argument("--install-dir")
    args = parser.parse_args()

    temp_launcher: Path | None = None
    should_pause = args.relaunch

    try:
        context = infer_install_context(args.install_dir)
        install_dir = context.install_dir
        source = context.source
        current_exe = Path(sys.executable).resolve()
        if not args.relaunch and current_exe.parent == install_dir:
            temp_launcher = Path(tempfile.mkdtemp(prefix=f"{APP_NAME}-uninstaller-")) / uninstaller_exe_name()
            shutil.copy2(current_exe, temp_launcher)
            print(f"[{APP_NAME}] Restarting uninstaller from a temporary location...")
            subprocess.Popen(
                [str(temp_launcher), "--relaunch", "--install-dir", str(install_dir)],
                cwd=temp_launcher.parent,
            )
            return

        install_dir = assert_safe_app_dir(install_dir)
        start_menu_dir = (
            assert_safe_start_menu_dir(Path(context.metadata.start_menu_dir))
            if context.metadata and context.metadata.start_menu_dir
            else None
        )
        installer_dir = Path(metadata_path()).parent

        print("")
        print(f"Inferred install path from {source}:")
        print(f"  {install_dir}")
        print("")
        print("This will remove:")
        print(f"  App folder: {install_dir}")
        if start_menu_dir is not None:
            print(f"  Start Menu folder: {start_menu_dir}")
        print("")

        choice = input("Type REMOVE to continue or CANCEL to stop\n> ").strip()
        if choice != "REMOVE":
            print(f"[{APP_NAME}] Uninstall cancelled.")
            return

        if install_dir.exists():
            print(f"[{APP_NAME}] Removing installed files...")
            shutil.rmtree(install_dir, ignore_errors=False)
        if start_menu_dir is not None and start_menu_dir.exists():
            print(f"[{APP_NAME}] Removing Start Menu shortcuts...")
            shutil.rmtree(start_menu_dir, ignore_errors=False)
        if context.metadata is not None and installer_dir.exists():
            print(f"[{APP_NAME}] Removing installer metadata...")
            shutil.rmtree(installer_dir, ignore_errors=True)

        print(f"[{APP_NAME}] Uninstall complete.")
    except Exception as exc:
        print("")
        print(f"Uninstall failed: {exc}", file=sys.stderr)
    finally:
        if temp_launcher and temp_launcher.parent.exists():
            shutil.rmtree(temp_launcher.parent, ignore_errors=True)
        if should_pause:
            pause()


def metadata_path() -> Path:
    from ytdlp_tui.core.windows_installer import metadata_path as _metadata_path

    return _metadata_path()


if __name__ == "__main__":
    run()
