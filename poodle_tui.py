from textual.app import App, ComposeResult, RenderResult
from textual.widget import Widget
from textual.widgets import Footer, Welcome, Static, RichLog, Pretty

import pyfiglet
from rich.console import Console

console = Console()


class Hello(Static):
    def welcome(self):
        f = pyfiglet.figlet_format("poodle.", font="slant")
        with console.capture() as w:
            console.print(
                f"{f}[bright_magenta]Voice interface GPT in your terminal.[/bright_magenta]"
            )
        return w.get()

    def render(self) -> RenderResult:
        return self.welcome()


class PoodleTui(App):
    BINDINGS = [("d", "toggle_dark", "Dark mode"), ("e", "hide_welcome", "bla")]

    def compose(self) -> ComposeResult:
        yield Hello()
        yield RichLog(
            markup=True,
            highlight=True,
            auto_scroll=True,
            wrap=True,
        )
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_hide_welcome(self):
        self.query_one(Hello).visible = False


if __name__ == "__main__":
    app = PoodleTui()
    app.run()
