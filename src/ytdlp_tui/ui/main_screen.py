from pathlib import Path
import threading
from typing import TYPE_CHECKING

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
    last_request: DownloadRequest | None = None
    cancel_event: threading.Event | None = None
    download_in_progress: bool = False

    def compose(self):
        app = self.app

        yield Header()
        yield VerticalScroll(
            Static("Download", classes="title"),
            Static("Paste one or more URLs or search terms to begin.", classes="subtitle"),
            Vertical(
                Horizontal(
                    UrlInput(id="input_group"),
                    Select(
                        [
                            ("MP3", "mp3"),
                            ("OGG", "ogg"),
                            ("MP4", "mp4"),
                            ("WebM", "webm"),
                        ],
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
                    id="source_row",
                ),
                Static(
                    "Multiple inputs supported: separate with spaces, commas, semicolons, or new lines.",
                    classes="note tight-note",
                ),
                Vertical(
                    Horizontal(
                        Button("Download", id="download_button", variant="primary"),
                        Button("Cancel", id="cancel_download_button"),
                        Button("Retry Latest", id="retry_download_button"),
                        Button("Open Folder", id="open_folder_button"),
                        Button("Settings", id="settings_button"),
                        classes="actions action-row",
                        id="main_actions_wide",
                    ),
                    Horizontal(
                        Button("Download", id="download_button_compact", variant="primary"),
                        Button("Cancel", id="cancel_download_button_compact"),
                        Button("Retry Latest", id="retry_download_button_compact"),
                        classes="actions action-row",
                        id="main_actions_compact_primary",
                    ),
                    Horizontal(
                        Button("Open Folder", id="open_folder_button_compact"),
                        Button("Settings", id="settings_button_compact"),
                        classes="actions action-row",
                        id="main_actions_compact_secondary",
                    ),
                    id="main_actions_block",
                ),
                classes="main-toolbar",
            ),
            Horizontal(
                Vertical(
                    Vertical(
                        Static("Status", classes="section-title"),
                        Static(
                            "Ready for a download request.",
                            id="status_text",
                            classes="status-note status-box",
                        ),
                        Static(
                            f"Downloads will go to: {app.config.download_dir}",
                            id="download_dir_text",
                            classes="note tight-note",
                        ),
                        Static("", id="dependency_text", classes="note"),
                        classes="section-block",
                    ),
                    Vertical(
                        Static("Recent Result", classes="section-title"),
                        Horizontal(
                            Button("Open Latest File", id="open_latest_file_button"),
                            Button("Open Latest File Folder", id="open_latest_file_folder_button"),
                            classes="actions",
                            id="recent_actions",
                        ),
                        Static("", id="recent_files_text", classes="note status-box"),
                        classes="section-block",
                    ),
                    classes="panel-surface",
                    id="main_left",
                ),
                Vertical(
                    Static("Activity", classes="section-title"),
                    Static("", id="log_text", classes="note status-box"),
                    classes="panel-surface",
                    id="main_right",
                ),
                id="main_columns",
            ),
            id="main_panel",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_status()
        self._update_layout_mode()

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
        elif event.button.id in {"settings_button", "settings_button_compact"}:
            self.action_settings()
        elif event.button.id in {"open_folder_button", "open_folder_button_compact"}:
            self._open_download_dir()
        elif event.button.id == "open_latest_file_button":
            self._open_latest_file()
        elif event.button.id == "open_latest_file_folder_button":
            self._open_latest_file_folder()
        elif event.button.id in {"download_button", "download_button_compact"}:
            self._prepare_download()
        elif event.button.id in {"cancel_download_button", "cancel_download_button_compact"}:
            self._cancel_download()
        elif event.button.id in {"retry_download_button", "retry_download_button_compact"}:
            self._retry_latest_download()

    def _open_download_dir(self) -> None:
        app = self.app

        try:
            open_in_file_manager(app.config.download_dir)
            self.notify("Opened download folder in the system file manager.")
        except Exception as exc:
            self.notify(f"Could not open folder: {exc}", severity="error")

    def _clear_input(self) -> None:
        self.query_one("#input_group", UrlInput).clear()

    def on_screen_resume(self) -> None:
        app = self.app
        app.refresh_dependency_statuses()
        self.query_one("#download_dir_text", Static).update(
            f"Downloads will go to: {app.config.download_dir}"
        )
        self._refresh_status()

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
        status_widget.update(f"Starting download for {len(request.sources)} item(s)...")
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
        result = run_download(request, self.cancel_event)
        self.app.call_from_thread(self._apply_download_result, result)

    def _apply_download_result(self, result: DownloadResult) -> None:
        status_widget = self.query_one("#status_text", Static)
        log_widget = self.query_one("#log_text", Static)
        files_widget = self.query_one("#recent_files_text", Static)
        self.download_in_progress = False
        self.cancel_event = None
        self.recent_files = result.downloaded_files

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

    def _cancel_download(self) -> None:
        if not self.download_in_progress or self.cancel_event is None:
            self.notify("No download is running.", severity="warning")
            return

        self.cancel_event.set()
        self.query_one("#status_text", Static).update("Cancelling download...")
        self.notify("Cancelling download...")

    def _retry_latest_download(self) -> None:
        if self.download_in_progress:
            self.notify("Wait for the current download to finish or cancel it first.", severity="warning")
            return

        if self.last_request is None:
            self.notify("No previous download request is available.", severity="warning")
            return

        self.cancel_event = threading.Event()
        self.download_in_progress = True
        self.query_one("#status_text", Static).update("Retrying latest download...")
        self.query_one("#log_text", Static).update("")
        self._run_download(self.last_request)

    def _update_layout_mode(self) -> None:
        width = self.app.size.width
        compact = width < 136
        self.set_class(compact, "compact-layout")
