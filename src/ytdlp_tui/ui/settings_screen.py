from pathlib import Path

from textual import work
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from ytdlp_tui.core.config import AppConfig, get_default_downloads_dir
from ytdlp_tui.core.dependencies import install_managed_ytdlp
from ytdlp_tui.core.platform import dependency_policy_for_current_platform, open_in_file_manager


class SettingsScreen(Screen[None]):
    BINDINGS = [("escape", "pop_screen", "Back")]

    def compose(self):
        app = self.app

        config = app.config
        app.refresh_dependency_statuses()
        policy = dependency_policy_for_current_platform()

        yield Header()
        yield Vertical(
            Static("Settings", classes="title"),
            Static("Default download directory", classes="subtitle"),
            Input(
                value=config.download_dir,
                placeholder=get_default_downloads_dir(),
                id="download_dir_input",
            ),
            Button("Save", id="save_settings_button", variant="primary"),
            Button("Open Download Folder", id="open_download_dir_button"),
            Button("Install or Update yt-dlp", id="install_ytdlp_button"),
            Static(f"yt-dlp policy: {policy.ytdlp}", id="ytdlp_policy"),
            Static(f"ffmpeg policy: {policy.ffmpeg}", id="ffmpeg_policy"),
            Static(self._dependency_detail(app.ytdlp_status), id="ytdlp_detail", classes="note"),
            Static(self._dependency_detail(app.ffmpeg_status), id="ffmpeg_detail", classes="note"),
            Static(
                "Linux and macOS prefer user-installed tools. Windows defaults to managed downloads.",
                classes="note",
            ),
            id="settings_panel",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_settings_button":
            self._save_settings()
        elif event.button.id == "open_download_dir_button":
            self._open_download_dir()
        elif event.button.id == "install_ytdlp_button":
            self._install_ytdlp()

    def _save_settings(self) -> None:
        app = self.app

        download_dir = self.query_one("#download_dir_input", Input).value.strip()
        if not download_dir:
            self.notify("Download directory cannot be empty.", severity="error")
            return

        path = Path(download_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)

        app.update_config(AppConfig(download_dir=str(path)))
        app.refresh_dependency_statuses()
        self.notify("Settings saved.")

    def _open_download_dir(self) -> None:
        download_dir = self.query_one("#download_dir_input", Input).value.strip() or get_default_downloads_dir()
        path = Path(download_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)

        try:
            open_in_file_manager(path)
            self.notify("Opened download folder in the system file manager.")
        except Exception as exc:
            self.notify(f"Could not open folder: {exc}", severity="error")

    @work(thread=True)
    def _install_ytdlp(self) -> None:
        self.call_from_thread(self.notify, "Installing or updating managed yt-dlp...")
        try:
            status = install_managed_ytdlp()
        except Exception as exc:
            self.call_from_thread(self.notify, f"yt-dlp install failed: {exc}", severity="error")
            return

        self.call_from_thread(self._apply_ytdlp_status, status)

    def _apply_ytdlp_status(self, status) -> None:
        self.app.ytdlp_status = status
        self.query_one("#ytdlp_detail", Static).update(self._dependency_detail(status))
        self.notify("Managed yt-dlp is ready.")

    @staticmethod
    def _dependency_detail(status) -> str:
        if status.available:
            if status.path and status.version:
                return f"{status.path} ({status.version})"
            if status.path:
                return status.path
            return status.source
        return status.message or "Not available"
