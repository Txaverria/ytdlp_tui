from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from ytdlp_tui.core.config import get_default_downloads_dir, load_config
from ytdlp_tui.core.platform import dependency_policy_for_current_platform


class SettingsScreen(Screen[None]):
    BINDINGS = [("escape", "pop_screen", "Back")]

    def compose(self):
        config = load_config()
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
            Static(f"yt-dlp policy: {policy.ytdlp}", id="ytdlp_policy"),
            Static(f"ffmpeg policy: {policy.ffmpeg}", id="ffmpeg_policy"),
            Static("Settings persistence is scaffolded; save actions come in the next commit."),
            id="settings_panel",
        )
        yield Footer()
