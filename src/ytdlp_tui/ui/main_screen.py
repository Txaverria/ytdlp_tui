from pathlib import Path
from typing import TYPE_CHECKING

from textual import work
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Select, Static

from ytdlp_tui.core.downloads import validate_download_request
from ytdlp_tui.core.models import DownloadRequest, DownloadResult
from ytdlp_tui.core.platform import open_in_file_manager
from ytdlp_tui.core.runner import run_download

if TYPE_CHECKING:
    from ytdlp_tui.app import YtDlpTuiApp


class MainScreen(Screen[None]):
    BINDINGS = [("s", "settings", "Settings"), ("q", "quit", "Quit")]
    recent_files: list[str] = []

    def compose(self):
        app = self.app

        yield Header()
        yield Vertical(
            Static("Download", classes="title"),
            Static("Paste a URL or search term to begin.", classes="subtitle"),
            Input(placeholder="URL or search term", id="download_input"),
            Select(
                [("Audio", "audio"), ("Video", "video"), ("Custom", "custom")],
                value="video",
                id="mode_select",
                prompt="Mode",
            ),
            Horizontal(
                Button("Download", id="download_button", variant="primary"),
                Button("Open Folder", id="open_folder_button"),
                Button("Open Latest File", id="open_latest_file_button"),
                Button("Open Latest File Folder", id="open_latest_file_folder_button"),
                Button("Settings", id="settings_button"),
                classes="actions",
            ),
            Static(
                f"Downloads will go to: {app.config.download_dir}",
                id="download_dir_text",
                classes="note",
            ),
            Static(
                "This is the first scaffold for the rebuilt app. Download execution comes next.",
                id="status_text",
                classes="note",
            ),
            Static("", id="dependency_text", classes="note"),
            Static("", id="recent_files_text", classes="note"),
            Static("", id="log_text", classes="note"),
            id="main_panel",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_status()

    def action_settings(self) -> None:
        from ytdlp_tui.ui.settings_screen import SettingsScreen

        self.app.push_screen(SettingsScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings_button":
            self.action_settings()
        elif event.button.id == "open_folder_button":
            self._open_download_dir()
        elif event.button.id == "open_latest_file_button":
            self._open_latest_file()
        elif event.button.id == "open_latest_file_folder_button":
            self._open_latest_file_folder()
        elif event.button.id == "download_button":
            self._prepare_download()

    def _open_download_dir(self) -> None:
        app = self.app

        try:
            open_in_file_manager(app.config.download_dir)
            self.notify("Opened download folder in the system file manager.")
        except Exception as exc:
            self.notify(f"Could not open folder: {exc}", severity="error")

    def on_screen_resume(self) -> None:
        app = self.app
        app.refresh_dependency_statuses()
        self.query_one("#download_dir_text", Static).update(
            f"Downloads will go to: {app.config.download_dir}"
        )
        self._refresh_status()

    def _prepare_download(self) -> None:
        source = self.query_one("#download_input", Input).value
        mode = self.query_one("#mode_select", Select).value
        request = DownloadRequest(
            source=source,
            mode=str(mode),
            download_dir=self.app.config.download_dir,
        )

        errors = validate_download_request(request)
        status_widget = self.query_one("#status_text", Static)
        if errors:
            status_widget.update("\n".join(errors))
            self.notify(errors[0], severity="error")
            return

        status_widget.update("Starting download...")
        self.query_one("#log_text", Static).update("")
        self.query_one("#recent_files_text", Static).update("")
        self._run_download(request)

    def _refresh_status(self) -> None:
        app = self.app
        dependency_widget = self.query_one("#dependency_text", Static)
        dependency_widget.update(
            "\n".join(
                [
                    self._format_dependency("yt-dlp", app.ytdlp_status),
                    self._format_dependency("ffmpeg", app.ffmpeg_status),
                ]
            )
        )

    @staticmethod
    def _format_dependency(name: str, status) -> str:
        if status.available:
            detail = f"{status.source}"
            if status.version:
                detail += f", {status.version}"
            return f"{name}: {detail}"
        return f"{name}: {status.message or 'missing'}"

    @work(thread=True)
    def _run_download(self, request: DownloadRequest) -> None:
        result = run_download(request)
        self.call_from_thread(self._apply_download_result, result)

    def _apply_download_result(self, result: DownloadResult) -> None:
        status_widget = self.query_one("#status_text", Static)
        log_widget = self.query_one("#log_text", Static)
        files_widget = self.query_one("#recent_files_text", Static)
        self.recent_files = result.downloaded_files

        if result.success:
            status_widget.update(result.summary or "Download finished.")
            self.notify("Download finished.")
        else:
            status_widget.update(result.summary or result.error or "Download failed.")
            self.notify(result.error or "Download failed.", severity="error")

        if result.downloaded_files:
            files_widget.update(
                "Recent files:\n" + "\n".join(f"- {path}" for path in result.downloaded_files)
            )
        else:
            files_widget.update("")

        if result.output:
            tail = result.output[-20:]
            header = "Log:"
            if result.progress_line:
                header = f"Latest progress: {result.progress_line}\n\nLog:"
            log_widget.update(header + "\n" + "\n".join(tail))
        else:
            log_widget.update("")

    def _open_latest_file(self) -> None:
        latest = self._latest_file()
        if not latest:
            self.notify("No downloaded file is available yet.", severity="warning")
            return

        try:
            open_in_file_manager(latest)
            self.notify("Opened latest downloaded file.")
        except Exception as exc:
            self.notify(f"Could not open file: {exc}", severity="error")

    def _open_latest_file_folder(self) -> None:
        latest = self._latest_file()
        if not latest:
            self.notify("No downloaded file is available yet.", severity="warning")
            return

        try:
            open_in_file_manager(Path(latest).parent)
            self.notify("Opened latest file folder.")
        except Exception as exc:
            self.notify(f"Could not open folder: {exc}", severity="error")

    def _latest_file(self) -> str | None:
        return self.recent_files[-1] if self.recent_files else None
