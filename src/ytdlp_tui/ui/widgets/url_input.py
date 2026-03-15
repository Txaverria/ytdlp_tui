from textual.widget import Widget
from textual.widgets import Input


class UrlInput(Widget):
    DEFAULT_CSS = """
    UrlInput {
        width: 1fr;
        height: auto;
    }

    UrlInput Input {
        width: 1fr;
    }
    """

    def compose(self):
        yield Input(
            placeholder="URL or search term, separated by spaces, commas, semicolons, or newlines",
            id="download_input",
        )

    @property
    def input(self) -> Input:
        return self.query_one("#download_input", Input)

    def clear(self) -> None:
        self.input.value = ""
        self.input.focus()
