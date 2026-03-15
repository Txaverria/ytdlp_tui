from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static


class MainScreen(Screen[None]):
    BINDINGS = [("s", "settings", "Settings"), ("q", "quit", "Quit")]

    def compose(self):
        yield Header()
        yield Vertical(
            Static("Download", classes="title"),
            Static("Paste a URL or search term to begin.", classes="subtitle"),
            Input(placeholder="URL or search term", id="download_input"),
            Horizontal(
                Button("Download", id="download_button", variant="primary"),
                Button("Settings", id="settings_button"),
                classes="actions",
            ),
            Static(
                "This is the first scaffold for the rebuilt app. Download execution comes next.",
                id="status_text",
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
