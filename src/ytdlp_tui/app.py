from textual.app import App

from ytdlp_tui.core.config import AppConfig, load_config, save_config
from ytdlp_tui.core.dependencies import detect_ffmpeg, detect_ytdlp
from ytdlp_tui.core.models import DependencyStatus

from ytdlp_tui.ui.main_screen import MainScreen


class YtDlpTuiApp(App[None]):
    TITLE = "ytdlp-tui"
    SUB_TITLE = "Cross-platform terminal UI for yt-dlp"
    CSS = """
    Screen {
        layout: vertical;
        background: #10151c;
        color: #f3efe6;
    }

    Header {
        background: #d96c2d;
        color: #10151c;
    }

    Footer {
        background: #18222d;
    }

    .title {
        text-style: bold;
        color: #f4b860;
        margin: 0 0 0 0;
    }

    .subtitle {
        color: #9fb3c8;
        margin: 0 0 0 0;
    }

    .section-title {
        text-style: bold;
        color: #7dd3c7;
        margin: 0 0 0 0;
    }

    #main_panel, #settings_panel {
        width: 1fr;
        max-width: 108;
        height: 1fr;
        margin: 0 1;
        padding: 0 1;
        border: round #35506b;
        background: #13202c;
        overflow-y: auto;
    }

    .actions {
        height: auto;
        margin: 0 0;
    }

    .section-block {
        margin: 0 0 0 0;
        padding: 0 0 0 0;
        border-bottom: solid #223243;
    }

    .status-box {
        margin: 0 0 0 0;
        padding: 0 1;
        min-height: 1;
        border: round #35506b;
        background: #0d1721;
    }

    Button {
        margin-right: 1;
        margin-bottom: 0;
    }

    Input {
        margin: 0 0 0 0;
    }

    Select {
        margin: 0 0 0 0;
    }

    .note {
        color: #c7d3df;
    }

    .status-note {
        color: #f3efe6;
    }
    """

    def on_mount(self) -> None:
        self.config = load_config()
        self.refresh_dependency_statuses()
        self.push_screen(MainScreen())

    config: AppConfig
    ytdlp_status: DependencyStatus
    ffmpeg_status: DependencyStatus

    def update_config(self, config: AppConfig) -> None:
        self.config = config
        save_config(config)

    def refresh_dependency_statuses(self) -> None:
        self.ytdlp_status = detect_ytdlp()
        self.ffmpeg_status = detect_ffmpeg()
