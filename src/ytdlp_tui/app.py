from textual.app import App

from ytdlp_tui.core.config import AppConfig, load_config, save_config
from ytdlp_tui.core.dependencies import detect_ffmpeg, detect_ytdlp
from ytdlp_tui.core.models import DependencyStatus

from ytdlp_tui.ui.main_screen import MainScreen


class YtDlpTuiApp(App[None]):
    TITLE = "ytdlp-tui"
    CSS = """
    Screen {
        layout: vertical;
    }

    Header {
        background: $primary;
        color: $text;
    }

    Footer {
        background: $surface;
    }

    .title {
        text-style: bold;
        margin: 0 0 0 0;
    }

    .subtitle {
        color: $text-muted;
        margin: 0 0 0 0;
    }

    .hero {
        text-style: bold;
        margin: 0 0 1 0;
    }

    #main_panel, #settings_panel {
        width: 1fr;
        height: 1fr;
        margin: 0 1;
        padding: 0 1;
        overflow-y: auto;
    }

    .actions {
        height: auto;
        margin: 0 0;
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
        color: $text-muted;
    }

    Log#log_widget {
        border: round $panel-lighten-1;
        min-height: 12;
        height: auto;
        margin: 0 0 1 0;
        background: $panel;
        color: $text-muted;
    }

    .muted {
        color: $text-muted;
    }

    .spacer {
        height: 1;
    }

    .main-toolbar {
        height: auto;
        margin: 0 0 0 0;
    }

    #status_row {
        layout: horizontal;
        height: auto;
        align-vertical: middle;
    }

    #status_message_group {
        layout: horizontal;
        width: auto;
        height: auto;
        align-vertical: middle;
    }

    #status_text {
        width: auto;
    }

    ProgressBar#download_progress {
        width: 24;
        min-width: 24;
        margin-right: 1;
    }

    LoadingIndicator#status_loading {
        width: 8;
        margin-left: 1;
    }

    #source_row {
        layout: horizontal;
        height: auto;
        margin: 0 0 1 0;
    }

    #input_group {
        width: 1fr;
        margin-right: 1;
    }

    #format_select,
    #quality_select {
        width: 25;
        margin-right: 1;
    }

    #quality_select {
        margin-right: 0;
    }

    #main_columns {
        layout: vertical;
        height: auto;
    }

    .tight-note {
        margin: 0 0 0 0;
    }

    #main_actions_block {
        height: auto;
    }

    #primary_row {
        layout: horizontal;
        height: auto;
        margin: 0 0 1 0;
    }

    #input_row {
        height: auto;
        margin: 0 0 1 0;
    }

    #input_row #input_group {
        width: 1fr;
        margin-right: 0;
    }

    #primary_download_button {
        width: 12;
    }

    #secondary_row {
        layout: horizontal;
        height: auto;
        margin: 0 0 1 0;
    }

    #secondary_row Select {
        width: 16;
        margin-right: 1;
    }

    #secondary_settings_button {
        width: 12;
    }

    #recent_result {
        margin: 0 0 1 0;
    }

    #activity_log {
        color: #c7d3df;
        min-height: 12;
        height: auto;
    }

    .compact-layout #input_row #input_group {
        width: 1fr;
        margin-right: 0;
    }
    """

    def on_mount(self) -> None:
        self.config = load_config()
        self.refresh_dependency_statuses()
        self.theme_changed_signal.subscribe(self, self._refresh_theme_dependent_widgets)
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

    def _refresh_theme_dependent_widgets(self, _theme) -> None:
        for screen in self.screen_stack:
            refresh_for_theme = getattr(screen, "refresh_for_theme", None)
            if callable(refresh_for_theme):
                refresh_for_theme()
