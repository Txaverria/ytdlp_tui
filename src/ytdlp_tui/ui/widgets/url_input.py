from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button, Input


class UrlInput(Widget):
    DEFAULT_CSS = """
    UrlInput {
        width: 1fr;
        height: auto;
    }

    UrlInput > Horizontal {
        width: 1fr;
        height: auto;
    }

    UrlInput Input {
        width: 1fr;
        margin-right: 1;
    }

    UrlInput Button {
        width: 5;
        min-width: 3;
        height: 3;
        padding: 0;
        content-align: center middle;
        margin-right: 0;
    }
    """

    def compose(self):
        yield Horizontal(
            Input(placeholder="URL or search term", id="download_input"),
            Button("X", id="clear_input_button", variant="error"),
        )

    @property
    def input(self) -> Input:
        return self.query_one("#download_input", Input)

    def clear(self) -> None:
        self.input.value = ""
        self.input.focus()
