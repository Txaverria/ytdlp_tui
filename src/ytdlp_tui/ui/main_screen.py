from pathlib import Path
import threading
from typing import TYPE_CHECKING

from rich.text import Text
from textual import work
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Select, Static

from ytdlp_tui.core.downloads import parse_sources, validate_download_request
from ytdlp_tui.core.models import DownloadRequest, DownloadResult
from ytdlp_tui.core.platform import open_in_file_manager
from ytdlp_tui.core.runner import run_download
from ytdlp_tui.ui.widgets.url_input import UrlInput

if TYPE_CHECKING:
    from ytdlp_tui.app import YtDlpTuiApp


class MainScreen(Screen[None]):
    BINDINGS = [("s", "settings", "Settings"), ("ctrl+q", "quit_app", "Quit")]
    recent_files: list[str] = []
    log_lines: list[str] = []
    last_request: DownloadRequest | None = None
    cancel_event: threading.Event | None = None
    download_in_progress: bool = False

    @staticmethod
    def _build_hero(compact: bool) -> Text:
        if compact:
            raw = (
                "                                                     \n"
                "                                                     \n"
                "██  ██ ██████ ████▄  ██     █████▄         ██  ██ ██ \n"
                " ▀██▀    ██   ██  ██ ██     ██▄▄█▀   ▄▄▄   ██  ██ ██ \n"
                "  ██     ██   ████▀  ██████ ██             ▀████▀ ██ \n"
                "                                                     \n"
            )
        else:
            raw = (
                " █████ █████ ███████████ ██████████   █████       ███████████                   ███████████ █████  █████ █████\n"
                "▒▒███ ▒▒███ ▒█▒▒▒███▒▒▒█▒▒███▒▒▒▒███ ▒▒███       ▒▒███▒▒▒▒▒███                 ▒█▒▒▒███▒▒▒█▒▒███  ▒▒███ ▒▒███ \n"
                " ▒▒███ ███  ▒   ▒███  ▒  ▒███   ▒▒███ ▒███        ▒███    ▒███                 ▒   ▒███  ▒  ▒███   ▒███  ▒███ \n"
                "  ▒▒█████       ▒███     ▒███    ▒███ ▒███        ▒██████████     ██████████       ▒███     ▒███   ▒███  ▒███ \n"
                "   ▒▒███        ▒███     ▒███    ▒███ ▒███        ▒███▒▒▒▒▒▒     ▒▒▒▒▒▒▒▒▒▒        ▒███     ▒███   ▒███  ▒███ \n"
                "    ▒███        ▒███     ▒███    ███  ▒███      █ ▒███                             ▒███     ▒███   ▒███  ▒███ \n"
                "    █████       █████    ██████████   ███████████ █████                            █████    ▒▒████████   █████\n"
                "   ▒▒▒▒▒       ▒▒▒▒▒    ▒▒▒▒▒▒▒▒▒▒   ▒▒▒▒▒▒▒▒▒▒▒ ▒▒▒▒▒                            ▒▒▒▒▒      ▒▒▒▒▒▒▒▒   ▒▒▒▒▒\n"
            )

        text = Text()
        for char in raw:
            if char == "█":
                text.append(char, style="#cba6f7")
            elif char == "▒":
                text.append(char, style="#5a3c75")
            else:
                text.append(char, style="#cba6f7")
        return text

    def compose(self):
        app = self.app

        yield Header()
        yield VerticalScroll(
            Static("", classes="spacer"),
            Static(self._build_hero(False), classes="hero", id="hero_text"),
            Static("", id="status_meta", classes="muted"),
            Static("Ready.", id="status_text", classes="muted"),
            Static("", classes="spacer"),
            Vertical(
                Horizontal(
                    Select(
                        [("MP3", "mp3"), ("OGG", "ogg"), ("MP4", "mp4"), ("WebM", "webm")],
                        value="mp4",
                        id="format_select",
                        prompt="Format",
                    ),
                    Select(
                        [("High", "high"), ("Low", "low")],
                        value="high",
                        id="quality_select",
                        prompt="Quality",
                    ),
                    Button("Settings", id="settings_button"),
                    id="secondary_row",
                ),
                Horizontal(
                    UrlInput(id="input_group"),
                    id="input_row",
                ),
                Horizontal(
                    Button("Download", id="download_button", variant="primary"),
                    Button("Cancel", id="cancel_download_button"),
                    Button("Clear", id="clear_input_button"),
                    id="primary_row",
                ),
                classes="main-toolbar",
            ),
            Vertical(
                Horizontal(
                    Button("Open Latest File", id="open_latest_file_button"),
                    Button("Open Latest File Folder", id="open_latest_file_folder_button"),
                    id="recent_actions",
                ),
                Static("", id="recent_files_text", classes="note"),
                id="recent_result",
            ),
            Static("", id="log_text", classes="note",),
            id="main_panel",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_status()
        self._update_layout_mode()
        self._update_action_visibility()

    def on_resize(self) -> None:
        self._update_layout_mode()

    def action_settings(self) -> None:
        from ytdlp_tui.ui.settings_screen import SettingsScreen

        self.app.push_screen(SettingsScreen())

    def action_quit_app(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear_input_button":
            self._clear_input()
        elif event.button.id == "settings_button":
            self.action_settings()
        elif event.button.id == "open_latest_file_button":
            self._open_latest_file()
        elif event.button.id == "open_latest_file_folder_button":
            self._open_latest_file_folder()
        elif event.button.id == "download_button":
            self._prepare_download()
        elif event.button.id == "cancel_download_button":
            self._cancel_download()

    def _clear_input(self) -> None:
        self.query_one("#input_group", UrlInput).clear()

    def on_screen_resume(self) -> None:
        app = self.app
        app.refresh_dependency_statuses()
        self._refresh_status()
        self._update_action_visibility()

    def _prepare_download(self) -> None:
        if self.download_in_progress:
            self.notify("A download is already running.", severity="warning")
            return

        raw_input = self.query_one("#input_group", UrlInput).input.value
        output_format = self.query_one("#format_select", Select).value
        quality = self.query_one("#quality_select", Select).value
        request = DownloadRequest(
            sources=parse_sources(raw_input),
            output_format=str(output_format),
            quality=str(quality),
            download_dir=self.app.config.download_dir,
        )

        errors = validate_download_request(request)
        status_widget = self.query_one("#status_text", Static)
        if errors:
            status_widget.update("\n".join(errors))
            self.notify(errors[0], severity="error")
            return

        self.last_request = request
        self.cancel_event = threading.Event()
        self.download_in_progress = True
        self.log_lines = []
        status_widget.update(f"Starting download for {len(request.sources)} item(s)...")
        self.query_one("#log_text", Static).update("")
        self.query_one("#recent_files_text", Static).update("")
        self._update_action_visibility()
        self._run_download(request)

    def _refresh_status(self) -> None:
        app = self.app
        status_meta = self.query_one("#status_meta", Static)
        status_meta.update(
            "\n".join(
                [
                    self._format_dependency("yt-dlp", app.ytdlp_status),
                    self._format_dependency("FFmpeg", app.ffmpeg_status),
                    f"Downloads: {app.config.download_dir}",
                ]
            )
        )

    @staticmethod
    def _format_dependency(name: str, status) -> str:
        if status.available:
            return f"{name}: found"
        return f"{name}: not found"

    @work(thread=True)
    def _run_download(self, request: DownloadRequest) -> None:
        result = run_download(request, self.cancel_event, self._emit_live_output)
        self.app.call_from_thread(self._apply_download_result, result)

    def _emit_live_output(self, line: str) -> None:
        self.app.call_from_thread(self._append_log_line, line)

    def _append_log_line(self, line: str) -> None:
        self.log_lines.append(line)
        self.log_lines = self.log_lines[-20:]

        status_widget = self.query_one("#status_text", Static)
        if line.startswith("[download]"):
            status_widget.update(line)

        header = "Activity:"
        if self.log_lines and self.log_lines[-1].startswith("[download]"):
            header = f"Latest progress: {self.log_lines[-1]}\n\nActivity:"

        self.query_one("#log_text", Static).update(header + "\n" + "\n".join(self.log_lines))

    def _apply_download_result(self, result: DownloadResult) -> None:
        status_widget = self.query_one("#status_text", Static)
        log_widget = self.query_one("#log_text", Static)
        files_widget = self.query_one("#recent_files_text", Static)
        self.download_in_progress = False
        self.cancel_event = None
        self.recent_files = result.downloaded_files
        self._update_action_visibility()

        if result.cancelled:
            status_widget.update(result.summary or "Download cancelled.")
            self.notify("Download cancelled.", severity="warning")
        elif result.success:
            status_widget.update(result.summary or "Download finished.")
            self.notify("Download finished.")
        else:
            status_widget.update(result.summary or result.error or "Download failed.")
            self.notify(result.error or "Download failed.", severity="error")

        if result.downloaded_files:
            files_widget.update("Recent files:\n" + "\n".join(f"- {path}" for path in result.downloaded_files))
        else:
            files_widget.update("")

        if result.output:
            tail = result.output[-20:]
            header = "Activity:"
            if result.progress_line:
                header = f"Latest progress: {result.progress_line}\n\nActivity:"
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

    def _cancel_download(self) -> None:
        if not self.download_in_progress or self.cancel_event is None:
            self.notify("No download is running.", severity="warning")
            return

        self.cancel_event.set()
        self.query_one("#status_text", Static).update("Cancelling download...")
        self.notify("Cancelling download...")

    def _update_action_visibility(self) -> None:
        self.query_one("#download_button", Button).display = not self.download_in_progress
        self.query_one("#cancel_download_button", Button).display = self.download_in_progress
        self.query_one("#recent_result", Vertical).display = bool(self.recent_files)

    def _update_layout_mode(self) -> None:
        width = self.app.size.width
        compact = width < 136
        self.set_class(compact, "compact-layout")
        self.query_one("#hero_text", Static).update(self._build_hero(compact))
