# poodle_tui.py
from textual.app import App, ComposeResult, RenderResult
from textual.scroll_view import ScrollView
from textual.widget import Widget
from textual.containers import Grid
from textual.widgets import Footer, Static, RichLog, Input, Label, TextArea
from textual.reactive import Reactive
from textual import work
from textual import on
from rich.text import Text
from rich.spinner import Spinner
from rich.highlighter import ReprHighlighter
from rich.console import RenderableType
from rich.console import RenderableType
from rich.highlighter import ReprHighlighter
from rich.pretty import Pretty
from rich.protocol import is_renderable
from rich.text import Text
from typing import cast
import pyfiglet
from rich.markdown import Markdown
import config
from core.core import Poodle
from vui.audio_utils import (
    playMp3Sound,
)
from core.file_manager import FileManager
import event_flags as ef
from vui.vui import Vui


class SpinnerWidget(Widget):
    spinner = Spinner("dots", "Loading...", style="magenta")
    message = Reactive("")

    def activate(self, message="Loading..."):
        self.message = message
        self.spinner.text = Text.from_markup(f"[b]{message}[/b]", style="yellow")
        self.visible = True
        self.refresh()

    def deactivate(self):
        self.visible = False
        self.refresh()

    def render(self):
        if self.visible:
            return self.spinner
        else:
            return Text("")


class RichTextInput(TextArea):
    BINDINGS = [
        ("escape", "close", "close"),
        ("ctrl+d", "close", "close"),
        ("ctrl+s", "submit", "submit"),
    ]

    def action_submit(self):
        self.action_close()

    def action_close(self):
        self.remove()


class TextInput(Input):
    BINDINGS = [("escape", "close", "close"), ("ctrl+d", "close", "close")]

    def action_close(self):
        self.remove()


class DisplayMessage(Static):
    def __init__(
        self,
        content: RenderableType | object = None,
        classes="",
        id: str | None = None,
        icon="",
        str_style="",
    ):
        super().__init__()
        if id is not None:
            self.id = id
        self.str_style = str_style
        self.classes = classes
        self.content = content
        self.icon = icon
        self.highlighter = ReprHighlighter()

    def _make_renderable(self, content: RenderableType | object) -> RenderableType:
        renderable: RenderableType
        if isinstance(content, str):
            renderable = Text.from_markup(content, style=self.str_style)
            renderable = self.highlighter(renderable)
        else:
            renderable = cast(RenderableType, content)

        return renderable

    def compose(self):
        yield Label(self._make_renderable(self.icon), id="icons")
        yield Label(self._make_renderable(self.content), id="messages")


class DisplayUserMessage(DisplayMessage):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.content = kwargs.get("content")
        self.icon = kwargs.get("icon")
        self.str_style = "bright_magenta"

    def compose(self):
        yield Label(self._make_renderable(self.content), id="userMessages")
        yield Label(self._make_renderable(self.icon), id="icons")


class DisplayAssistantMessage(DisplayMessage):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.content = kwargs.get("content")
        self.icon = kwargs.get("icon")
        self.str_style = "cyan"

    def compose(self):
        yield Label(self._make_renderable(self.icon), id="icons")
        yield Label(self._make_renderable(self.content), id="assistantMessages")


class PoodleTui(App):

    CSS_PATH = "poodle_tui.tcss"

    BINDINGS = [
        ("k", "toggle_kw_detection", "toggle kw"),
        ("ctrl+s", "send", f"send to {config.KEYWORD}"),
        ("s", "input_speech, print_keyword_message", f"input speech"),
        ("i", "input_text", "input text"),
        ("v", "toggle_voice", "toggle voice"),
        ("u", "input_file", "upload file"),
    ]

    async def on_load(self):
        self.poodle = Poodle(config)
        self.poodle.run()
        self.chat_session = self.poodle.get_session()
        self.kw_listeners = [
            self.action_input_speech,
            self.action_print_keyword_message,
        ]
        self.poodle_vui = Vui(config.KEYWORD, self.kw_listeners, [])
        self.transcriber = self.poodle_vui.transcriber
        self.keyword_detector = self.poodle_vui.initialize_kw_detector()
        self.tts = self.poodle_vui.tts
        self.tts_local = self.poodle_vui.tts_local
        ef.silence.clear()
        ef.speaking.clear()
        self.chat_utils = self.poodle.chat_utils
        await self.poodle_vui.start_keyword_detection()
        self.transcriber_loop = self.set_interval(0.1, self.loop_transcription)
        self.n_chat_io = 0

    def on_mount(self):
        self.mount(DisplayMessage(self.welcome(), "hello", "hello"))
        if config.SOUNDS:
            # notification-sound-7062.mp3
            playMp3Sound("./sounds/ready.mp3")

    auto_send = Reactive(False)

    def compose(self) -> ComposeResult:
        yield Footer()

    def welcome(self):
        f = pyfiglet.figlet_format("poodle.", font="slant")
        w = str(
            f"{f}[bright_magenta]Voice interface GPT in your terminal.[/bright_magenta]"
            "\n                                v0.04"
        )
        return w

    def isSpeak(self):
        if (
            config.SPEAK is not None
            or config.SPEAK != ""
            or config.SPEAK.lower() != "none"
        ):
            return True
        return False

    @work
    async def log_response(self, resp, chat_utils):
        tstamp = FileManager.get_datetime_string()
        FileManager.save_json(
            f"{config.RESPONSE_LOG_PATH}response_{tstamp}.json",
            chat_utils.chat_completion_to_dict(resp),
        )

    def print_response(self, content: str):
        self.n_chat_io = self.n_chat_io + 1
        if not self.isSpeak():
            content_md = Markdown(str(content))
            self.mount(
                DisplayMessage(content_md, classes=f"response-message", icon=" 󰚩 > ")
            )
        else:
            self.mount(
                DisplayMessage(content, classes=f"response-message", icon=" 󰚩 > ")
            )

    def handle_response(self, resp, chat):
        tts_thread = None
        content = self.chat_utils.handle_response(resp, chat)
        if self.isSpeak():
            tts_thread = self.poodle_vui.speak_response(content)
            tts_thread.start()
        self.print_response(content)
        if tts_thread is not None:
            tts_thread.join()

    @work(exclusive=True)
    async def send_messages(self, chat):
        resp = await chat.send_chat_request()
        self.handle_response(resp, chat)

    @work(exclusive=True)
    async def add_chat_file(self, chat, file_dir):
        await chat.add_chat_file(file_dir)

    def loop_transcription(self) -> None:
        if ef.silence.is_set() and not ef.recording.is_set():
            self.poodle_vui.process_transcriptions()
            transcriptions: list = self.poodle_vui.get_transcriptions()
            trans_text = self.chat_utils.extract_trans_text(transcriptions)
            if len(trans_text) == 0:
                if config.SOUNDS:
                    playMp3Sound("./sounds/badcopy.mp3")
                self.mount(
                    DisplayMessage(
                        content=" I didn't hear you",
                        classes="local",
                    )
                )
                ef.silence.clear()
                return  # Exit the function early if there's no transcription
            if config.SOUNDS:

                playMp3Sound("./sounds/listening.mp3")
            self.n_chat_io = self.n_chat_io + 1
            self.mount(
                DisplayUserMessage(
                    trans_text[0], icon="[blue] < 󰔊 [/blue]", classes="local"
                )
            )
            if len(str(transcriptions)) != 0:
                self.chat_session.add_user_trans(transcriptions)
            if self.auto_send:
                self.action_send()

    def action_print_keyword_message(self, keyword, data, stream_write_time) -> None:
        self.mount(
            DisplayMessage(
                f"\n This is {keyword}. I am listening.",
                classes="local",
            )
        )
        if config.SOUNDS:
            playMp3Sound("./sounds/listening.mp3")
        if config.SPEAK.lower() == "cloud":
            if self.tts.is_audio_playing():
                self.tts.stop_audio()
        if config.SPEAK.lower() == "local":
            self.tts_local.stop_audio()
        else:
            pass

    def action_toggle_voice(self):
        self.mount(
            DisplayMessage(
                f"voice is set to {config.SPEAK}",
                classes="local",
            )
        )

    @on(Input.Submitted, "#text_input")
    def add_text_input(self):
        input = self.query_one("#text_input", TextInput)
        text = input.value
        self.chat_session.add_user_text(text)
        self.mount(
            DisplayUserMessage(
                content=text, classes=f"user-message", icon="[blue] < 󰯓  [/blue]"
            )
        )
        input.clear()

    @on(Input.Submitted, "#file_input")
    def add_file_input(self):
        input = self.query_one("#file_input", TextInput)
        file_dir = input.value
        self.add_chat_file(self.chat_session, file_dir)
        self.mount(
            DisplayUserMessage(
                content=file_dir, icon="[blue] < 󰛶  [/blue]", classes="user-file"
            )
        )
        input.clear()

    def action_input_file(self):
        new_input = TextInput(id="file_input")
        self.mount(new_input)
        new_input.focus()

    def action_input_text(self):
        new_input = TextInput(id="text_input")
        self.app.mount(new_input)
        new_input.focus()

    def action_input_speech(self, keyword, data, stream_write_time):
        self.poodle_vui.start_recording(stream_write_time)

    def action_send(self) -> None:
        self.mount(DisplayAssistantMessage("send it", classes="local"))
        self.send_messages(self.chat_session)

    async def action_toggle_kw_detection(self):
        if self.poodle_vui.keyword_detection_active:
            self.poodle_vui.stop_keyword_detection()
            self.mount(
                DisplayMessage(
                    "Keyword detection stopped.",
                    classes="local",
                )
            )
        else:
            await self.poodle_vui.start_keyword_detection()
            self.mount(
                DisplayMessage(
                    "Keyword detection started.",
                    classes="local",
                )
            )

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


if __name__ == "__main__":
    app = PoodleTui()
    app.run()
