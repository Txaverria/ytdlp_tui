from textual.app import App

from ytdlp_tui.ui.main_screen import MainScreen


class YtDlpTuiApp(App[None]):
    TITLE = "ytdlp-tui"
    SUB_TITLE = "Cross-platform terminal UI for yt-dlp"
    CSS = """
    Screen {
        layout: vertical;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(MainScreen())
