from textual import work
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, ProgressBar, Static
import re

from ytdlp_tui.core.config import AppConfig, get_default_downloads_dir
from ytdlp_tui.core.dependencies import install_managed_ffmpeg, install_managed_ytdlp
from ytdlp_tui.core.platform import current_platform, dependency_policy_for_current_platform


class SettingsScreen(Screen[None]):
    BINDINGS = [("escape", "back", "Back"), ("ctrl+q", "quit_app", "Quit")]
    PROGRESS_RE = re.compile(r"(\d+)%$")

    def compose(self):
        app = self.app

        config = app.config
        app.refresh_dependency_statuses()
        policy = dependency_policy_for_current_platform()

        yield Header()
        yield VerticalScroll(
            Static("", classes="spacer"),
            Static("Settings", classes="title"),
            Static("Configure where downloads go and how dependencies are managed.", classes="subtitle"),
            Static("", classes="spacer"),
            Static("Download Directory", classes="title"),
            Input(
                value=config.download_dir,
                placeholder=get_default_downloads_dir(),
                id="download_dir_input",
            ),
            Static("", classes="spacer"),
            Horizontal(
                Button("Save", id="save_settings_button", variant="primary"),
                Button("Set Default Downloads Folder", id="set_default_download_dir_button"),
                classes="actions",
            ),
            Static("", classes="spacer"),
            Static("Dependency Management", classes="title"),
            Static(f"yt-dlp policy: {policy.ytdlp}", id="ytdlp_policy", classes="note"),
            Static(self._dependency_detail(app.ytdlp_status), id="ytdlp_detail", classes="note"),
            Static("", classes="spacer"),
            Button("Install or Update yt-dlp", id="install_ytdlp_button"),
            ProgressBar(total=100, show_eta=False, show_percentage=False, id="ytdlp_progress"),
            Static("", classes="spacer"),
            Static(f"ffmpeg policy: {policy.ffmpeg}", id="ffmpeg_policy", classes="note"),
            Static(self._dependency_detail(app.ffmpeg_status), id="ffmpeg_detail", classes="note"),
            Static("", classes="spacer"),
            Button("Install or Update ffmpeg", id="install_ffmpeg_button"),
            ProgressBar(total=100, show_eta=False, show_percentage=False, id="ffmpeg_progress"),
            Static("", classes="spacer"),
            Static("YouTube Runtime", classes="title"),
            Static(self._deno_detail(app.deno_status), id="deno_detail", classes="note"),
            Static("Some YouTube downloads may require Deno.", classes="note"),
            Static("", classes="spacer"),
            Static(
                self._platform_dependency_note(),
                classes="note",
            ),
            id="settings_panel",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_settings_button":
            self._save_settings()
        elif event.button.id == "set_default_download_dir_button":
            self._set_default_download_dir()
        elif event.button.id == "install_ytdlp_button":
            self._install_ytdlp()
        elif event.button.id == "install_ffmpeg_button":
            self._install_ffmpeg()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_quit_app(self) -> None:
        self.app.action_quit()

    def _save_settings(self) -> None:
        app = self.app

        download_dir = self.query_one("#download_dir_input", Input).value.strip()
        if not download_dir:
            self.notify("Download directory cannot be empty.", severity="error")
            return

        path = Path(download_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)

        app.update_config(
            AppConfig(
                download_dir=str(path),
                output_format=app.config.output_format,
                quality=app.config.quality,
            )
        )
        app.refresh_dependency_statuses()
        self.notify("Settings saved.")

    def _set_default_download_dir(self) -> None:
        self.query_one("#download_dir_input", Input).value = get_default_downloads_dir()
        self.notify("Default Downloads folder restored.")

    @work(thread=True)
    def _install_ytdlp(self) -> None:
        self.app.call_from_thread(self._set_dependency_progress, "#ytdlp_detail", "Starting yt-dlp install...")
        try:
            status = install_managed_ytdlp(lambda message: self.app.call_from_thread(self._set_dependency_progress, "#ytdlp_detail", message))
        except Exception as exc:
            self.app.call_from_thread(self._set_dependency_progress, "#ytdlp_detail", self._dependency_detail(self.app.ytdlp_status))
            self.app.call_from_thread(self.notify, f"yt-dlp install failed: {exc}", severity="error")
            return

        self.app.call_from_thread(self._apply_ytdlp_status, status)

    def _apply_ytdlp_status(self, status) -> None:
        self.app.ytdlp_status = status
        self.query_one("#ytdlp_progress", ProgressBar).display = False
        self.query_one("#ytdlp_detail", Static).update(self._dependency_detail(status))
        self.notify("Managed yt-dlp is ready.")

    @work(thread=True)
    def _install_ffmpeg(self) -> None:
        self.app.call_from_thread(self._set_dependency_progress, "#ffmpeg_detail", "Starting ffmpeg install...")
        try:
            status = install_managed_ffmpeg(lambda message: self.app.call_from_thread(self._set_dependency_progress, "#ffmpeg_detail", message))
        except Exception as exc:
            self.app.call_from_thread(self._set_dependency_progress, "#ffmpeg_detail", self._dependency_detail(self.app.ffmpeg_status))
            self.app.call_from_thread(self.notify, f"ffmpeg install failed: {exc}", severity="error")
            return

        self.app.call_from_thread(self._apply_ffmpeg_status, status)

    def _apply_ffmpeg_status(self, status) -> None:
        self.app.ffmpeg_status = status
        self.query_one("#ffmpeg_progress", ProgressBar).display = False
        self.query_one("#ffmpeg_detail", Static).update(self._dependency_detail(status))
        self.notify("Managed ffmpeg is ready.")

    def _set_dependency_progress(self, selector: str, message: str) -> None:
        self.query_one(selector, Static).update(message)
        progress_id = "#ytdlp_progress" if selector == "#ytdlp_detail" else "#ffmpeg_progress"
        progress = self.query_one(progress_id, ProgressBar)
        progress.display = True
        parsed = self._extract_percent(message)
        if parsed is not None:
            progress.update(progress=parsed)
        elif any(keyword in message for keyword in ("Installing", "Extracting")):
            progress.update(progress=100)
        else:
            progress.update(progress=0)

    @staticmethod
    def _dependency_detail(status) -> str:
        if status.available:
            if status.path and status.version:
                return f"{status.path} ({status.version})"
            if status.path:
                return status.path
            return status.source
        return status.message or "Not available"

    @staticmethod
    def _platform_dependency_note() -> str:
        platform_name = current_platform()
        if platform_name == "windows":
            return "Windows defaults to managed yt-dlp and ffmpeg downloads."
        if platform_name == "macos":
            return "macOS prefers user-installed yt-dlp and ffmpeg."
        return "Linux prefers user-installed yt-dlp and ffmpeg."

    @staticmethod
    def _deno_detail(status) -> str:
        if status.available:
            version = status.version.splitlines()[0] if status.version else "found"
            return f"Deno: found ({version})"
        return "Deno: not found"

    @classmethod
    def _extract_percent(cls, message: str) -> float | None:
        match = cls.PROGRESS_RE.search(message)
        if not match:
            return None
        return float(match.group(1))
