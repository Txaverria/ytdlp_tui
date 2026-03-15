from textual import events
from textual.widget import Widget
from textual.widgets import Input


class PasteFriendlyInput(Input):
    def _on_paste(self, event: events.Paste) -> None:
        if event.text:
            flattened = " ".join(part.strip() for part in event.text.splitlines() if part.strip())
            self.insert_text_at_cursor(flattened)
        event.stop()
        event.prevent_default()


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
        yield PasteFriendlyInput(
            placeholder="URL or search term, separated by spaces, commas, semicolons, or newlines",
            id="download_input",
        )

    @property
    def input(self) -> Input:
        return self.query_one("#download_input", Input)

    def clear(self) -> None:
        self.input.value = ""
        self.input.focus()
