import threading
import re
from typing import TYPE_CHECKING

from rich.text import Text
from textual.color import Color
from textual import work
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, LoadingIndicator, Log, ProgressBar, Select, Static

from ytdlp_tui.core.downloads import parse_sources, validate_download_request
from ytdlp_tui.core.models import DownloadRequest, DownloadResult
from ytdlp_tui.core.runner import run_download
from ytdlp_tui.ui.widgets.url_input import UrlInput

if TYPE_CHECKING:
    from ytdlp_tui.app import YtDlpTuiApp


class MainScreen(Screen[None]):
    BINDINGS = [("s", "settings", "Settings"), ("ctrl+q", "quit_app", "Quit")]
    PROGRESS_RE = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")
    PHASE_MESSAGES = {
        "[FixupM4a]": "Fixing audio container...",
        "[ExtractAudio]": "Converting audio...",
        "[Merger]": "Merging streams...",
        "[VideoRemuxer]": "Remuxing file...",
    }
    recent_files: list[str] = []
    log_lines: list[str] = []
    last_request: DownloadRequest | None = None
    cancel_event: threading.Event | None = None
    download_in_progress: bool = False
    postprocess_active: bool = False

    def _hero_colors(self) -> tuple[str, str]:
        theme = self.app.current_theme
        base = Color.parse(theme.secondary or theme.primary or "#cba6f7")
        background = Color.parse(theme.background or theme.surface or "#181825")
        shaded = base.blend(background, 0.45)
        return base.hex6, shaded.hex6

    def _build_hero(self, compact: bool) -> Text:
        if compact:
            raw = (
                "██    ██ ████████ ██████  ██      ██████        ████████ ██    ██ ██ \n"
                " ██  ██     ██    ██   ██ ██      ██   ██          ██    ██    ██ ██ \n"
                "  ████      ██    ██   ██ ██      ██████  █████    ██    ██    ██ ██ \n"
                "   ██       ██    ██   ██ ██      ██               ██    ██    ██ ██ \n"
                "   ██       ██    ██████  ███████ ██               ██     ██████  ██ \n"
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

        solid_color, shaded_color = self._hero_colors()
        text = Text()
        for char in raw:
            if char == "█":
                text.append(char, style=solid_color)
            elif char == "▒":
                text.append(char, style=shaded_color)
            else:
                text.append(char, style=solid_color)
        return text

    def compose(self):
        app = self.app

        yield Header()
        yield VerticalScroll(
            Static("", classes="spacer"),
            Static(self._build_hero(False), classes="hero", id="hero_text"),
            Static("", id="status_meta"),
            Static("", classes="spacer"),
            Horizontal(
                ProgressBar(total=100, show_eta=False, show_percentage=False, id="download_progress"),
                Horizontal(
                    Static("Ready.", id="status_text"),
                    LoadingIndicator(id="status_loading"),
                    id="status_message_group",
                ),
                id="status_row",
            ),
            Static("", classes="spacer"),
            Vertical(
                Horizontal(
                    Select(
                        [("MP3", "mp3"), ("M4A", "m4a"), ("OGG", "ogg"), ("MP4", "mp4"), ("WebM", "webm")],
                        value="mp4",
                        id="format_select",
                        prompt="Format",
                    ),
                    Select(
                        [("High", "high"), ("Medium", "medium"), ("Low", "low")],
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
                    Button("Cancel", id="cancel_download_button", variant="warning"),
                    Button("Clear", id="clear_input_button"),
                    Button("Copy Log", id="copy_log_button"),
                    id="primary_row",
                ),
                classes="main-toolbar",
            ),
            Log(id="log_widget", auto_scroll=True),
            id="main_panel",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._sync_selects_from_config()
        self._refresh_status()
        self._update_layout_mode()
        self._update_action_visibility()

    def on_resize(self) -> None:
        self._update_layout_mode()

    def refresh_for_theme(self) -> None:
        self._update_layout_mode()
        self.refresh()

    def action_settings(self) -> None:
        from ytdlp_tui.ui.settings_screen import SettingsScreen

        self.app.push_screen(SettingsScreen())

    def action_quit_app(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear_input_button":
            self._clear_input()
        elif event.button.id == "copy_log_button":
            self._copy_log()
        elif event.button.id == "settings_button":
            self.action_settings()
        elif event.button.id == "download_button":
            self._prepare_download()
        elif event.button.id == "cancel_download_button":
            self._cancel_download()

    def _clear_input(self) -> None:
        self.query_one("#input_group", UrlInput).clear()
        self.log_lines = []
        self.postprocess_active = False
        self.query_one("#log_widget", Log).clear()
        self.query_one("#download_progress", ProgressBar).update(progress=0)
        self._update_action_visibility()

    def _copy_log(self) -> None:
        if not self.log_lines:
            self.notify("There is no log output to copy.", severity="warning")
            return
        self.app.copy_to_clipboard("\n".join(self.log_lines))
        self.notify("Log copied to clipboard.")

    def on_screen_resume(self) -> None:
        app = self.app
        app.refresh_dependency_statuses()
        self._sync_selects_from_config()
        self._update_layout_mode()
        self._refresh_status()
        self._update_action_visibility()

    def _prepare_download(self) -> None:
        if self.download_in_progress:
            self.notify("A download is already running.", severity="warning")
            return

        raw_input = self.query_one("#input_group", UrlInput).input.value
        format_select = self.query_one("#format_select", Select)
        quality_select = self.query_one("#quality_select", Select)
        output_format = format_select.value
        quality = quality_select.value
        status_widget = self.query_one("#status_text", Static)

        if output_format is Select.BLANK:
            status_widget.update("Select a format before downloading.")
            self.notify("Select a format before downloading.", severity="error")
            return

        if quality is Select.BLANK:
            status_widget.update("Select a quality before downloading.")
            self.notify("Select a quality before downloading.", severity="error")
            return

        request = DownloadRequest(
            sources=parse_sources(raw_input),
            output_format=str(output_format),
            quality=str(quality),
            download_dir=self.app.config.download_dir,
        )

        errors = validate_download_request(request)
        if errors:
            status_widget.update("\n".join(errors))
            self.notify(errors[0], severity="error")
            return

        self.last_request = request
        self.cancel_event = threading.Event()
        self.download_in_progress = True
        self.postprocess_active = False
        self.log_lines = []
        status_widget.update(f"Starting download for {len(request.sources)} item(s)...")
        self.query_one("#log_widget", Log).clear()
        self.query_one("#download_progress", ProgressBar).update(total=100, progress=0)
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
            self.postprocess_active = False
            status_widget.update(line)
            progress = self._extract_progress(line)
            if progress is not None:
                self.query_one("#download_progress", ProgressBar).update(progress=progress)
        else:
            phase_message = self._phase_status_message(line)
            if phase_message:
                self.postprocess_active = True
                status_widget.update(phase_message)
                self.query_one("#download_progress", ProgressBar).update(progress=100)

        self._update_action_visibility()

        log_widget = self.query_one("#log_widget", Log)
        log_widget.clear()
        for entry in self.log_lines:
            log_widget.write_line(entry)

    def _apply_download_result(self, result: DownloadResult) -> None:
        status_widget = self.query_one("#status_text", Static)
        log_widget = self.query_one("#log_widget", Log)
        self.download_in_progress = False
        self.postprocess_active = False
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

        if result.success:
            self.query_one("#download_progress", ProgressBar).update(progress=100)

        if result.output:
            tail = result.output[-20:]
            log_widget.clear()
            for entry in tail:
                log_widget.write_line(entry)
        else:
            log_widget.clear()

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
        self.query_one("#clear_input_button", Button).disabled = self.download_in_progress
        self.query_one("#copy_log_button", Button).display = bool(self.log_lines)
        has_log = self.download_in_progress or bool(self.log_lines)
        self.query_one("#download_progress", ProgressBar).display = self.download_in_progress and not self.postprocess_active
        self.query_one("#status_loading", LoadingIndicator).display = self.postprocess_active
        self.query_one("#log_widget", Log).display = has_log

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "download_input":
            return

        value = event.value
        normalized = value.replace("\r", " ").replace("\n", " ")
        if normalized != value:
            event.input.value = normalized

    def on_select_changed(self, event: Select.Changed) -> None:
        config = self.app.config
        changed = False

        if event.select.id == "format_select" and event.value is not Select.BLANK:
            config.output_format = str(event.value)
            changed = True
        elif event.select.id == "quality_select" and event.value is not Select.BLANK:
            config.quality = str(event.value)
            changed = True

        if changed:
            self.app.update_config(config)

    def _update_layout_mode(self) -> None:
        width = self.app.size.width
        compact = width < 136
        self.set_class(compact, "compact-layout")
        self.query_one("#hero_text", Static).update(self._build_hero(compact))

    def _sync_selects_from_config(self) -> None:
        config = self.app.config
        self.query_one("#format_select", Select).value = config.output_format
        self.query_one("#quality_select", Select).value = config.quality

    @classmethod
    def _extract_progress(cls, line: str) -> float | None:
        match = cls.PROGRESS_RE.search(line)
        if not match:
            return None
        return float(match.group(1))

    @classmethod
    def _phase_status_message(cls, line: str) -> str | None:
        for prefix, message in cls.PHASE_MESSAGES.items():
            if line.startswith(prefix):
                return message
        return None
