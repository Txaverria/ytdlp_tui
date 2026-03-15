from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ytdlp_tui.core.windows_installer import (
    APP_NAME,
    current_version,
    download_release_zip,
    ensure_app_not_running,
    fetch_latest_windows_release,
    find_bundle_dir,
    infer_install_context,
    InstallMetadata,
    pause,
    replace_app_dir,
    save_metadata,
    updater_exe_name,
)


def run() -> None:
    parser = argparse.ArgumentParser(prog=updater_exe_name())
    parser.add_argument("--relaunch", action="store_true")
    parser.add_argument("--install-dir")
    args = parser.parse_args()

    temp_launcher: Path | None = None
    temp_root: Path | None = None
    should_pause = args.relaunch

    try:
        context = infer_install_context(args.install_dir)
        install_dir = context.install_dir
        source = context.source

        current_exe = Path(sys.executable).resolve()
        if not args.relaunch and current_exe.parent == install_dir:
            temp_launcher = Path(tempfile.mkdtemp(prefix=f"{APP_NAME}-updater-")) / updater_exe_name()
            shutil.copy2(current_exe, temp_launcher)
            print(f"[{APP_NAME}] Restarting updater from a temporary location...")
            subprocess.Popen(
                [str(temp_launcher), "--relaunch", "--install-dir", str(install_dir)],
                cwd=temp_launcher.parent,
            )
            return

        ensure_app_not_running()

        metadata = context.metadata or InstallMetadata(
            app_name=APP_NAME,
            version="unknown",
            install_dir=str(install_dir),
            start_menu_dir="",
            app_shortcut="",
            update_shortcut="",
            uninstall_shortcut="",
        )
        release = fetch_latest_windows_release()

        print("")
        print(f"Inferred install path from {source}:")
        print(f"  {install_dir}")
        print("")
        print(f"Installed version: {metadata.version}")
        print(f"Latest version:    {release.version}")
        print("")

        if release.version == metadata.version:
            print(f"[{APP_NAME}] The app is already up to date.")
            return

        choice = input("Type UPDATE to continue or CANCEL to stop\n> ").strip()
        if choice != "UPDATE":
            print(f"[{APP_NAME}] Update cancelled.")
            return

        print(f"[{APP_NAME}] Downloading {release.version}...")
        temp_root, extract_dir = download_release_zip(release.url)
        print(f"[{APP_NAME}] Extracting release archive...")
        source_dir = find_bundle_dir(extract_dir)
        print(f"[{APP_NAME}] Updating installed app...")
        replace_app_dir(source_dir, install_dir)

        if context.metadata is not None:
            metadata.version = release.version
            save_metadata(metadata)
        print(f"[{APP_NAME}] Update complete.")
    except Exception as exc:
        print("")
        print(f"Update failed: {exc}", file=sys.stderr)
    finally:
        if temp_root and temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)
        if temp_launcher and temp_launcher.parent.exists():
            shutil.rmtree(temp_launcher.parent, ignore_errors=True)
        if should_pause:
            pause()


if __name__ == "__main__":
    run()
