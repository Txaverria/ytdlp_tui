from textual.app import App

from ytdlp_tui.core.config import AppConfig, load_config, save_config

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
        margin: 1 0 0 0;
    }

    .subtitle {
        color: #9fb3c8;
        margin: 0 0 1 0;
    }

    #main_panel, #settings_panel {
        width: 1fr;
        max-width: 90;
        height: auto;
        margin: 1 2;
        padding: 1 2;
        border: round #35506b;
        background: #13202c;
    }

    .actions {
        height: auto;
        margin: 1 0;
    }

    Button {
        margin-right: 1;
    }

    Input {
        margin: 0 0 1 0;
    }

    .note {
        color: #c7d3df;
    }
    """

    def on_mount(self) -> None:
        self.config = load_config()
        self.push_screen(MainScreen())

    config: AppConfig

    def update_config(self, config: AppConfig) -> None:
        self.config = config
        save_config(config)
