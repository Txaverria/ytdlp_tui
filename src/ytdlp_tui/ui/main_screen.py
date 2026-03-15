from typing import TYPE_CHECKING

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from ytdlp_tui.core.platform import open_in_file_manager

if TYPE_CHECKING:
    from ytdlp_tui.app import YtDlpTuiApp


class MainScreen(Screen[None]):
    BINDINGS = [("s", "settings", "Settings"), ("q", "quit", "Quit")]

    def compose(self):
        app = self.app

        yield Header()
        yield Vertical(
            Static("Download", classes="title"),
            Static("Paste a URL or search term to begin.", classes="subtitle"),
            Input(placeholder="URL or search term", id="download_input"),
            Horizontal(
                Button("Download", id="download_button", variant="primary"),
                Button("Open Folder", id="open_folder_button"),
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
            id="main_panel",
        )
        yield Footer()

    def action_settings(self) -> None:
        from ytdlp_tui.ui.settings_screen import SettingsScreen

        self.app.push_screen(SettingsScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings_button":
            self.action_settings()
        elif event.button.id == "open_folder_button":
            self._open_download_dir()
        elif event.button.id == "download_button":
            self.notify("Download execution is the next milestone.")

    def _open_download_dir(self) -> None:
        app = self.app

        try:
            open_in_file_manager(app.config.download_dir)
            self.notify("Opened download folder in the system file manager.")
        except Exception as exc:
            self.notify(f"Could not open folder: {exc}", severity="error")

    def on_screen_resume(self) -> None:
        app = self.app
        self.query_one("#download_dir_text", Static).update(
            f"Downloads will go to: {app.config.download_dir}"
        )
