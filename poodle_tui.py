# poodle_tui.py
from re import M
import textwrap
import time
from typing import cast

from config import Configurator
from core.core import Poodle
from core.file_manager import FileManager
import event_flags as ef
import pyfiglet
from rich.console import RenderableType
from rich.console import RenderableType
from rich.highlighter import ReprHighlighter
from rich.highlighter import ReprHighlighter
from rich.progress import BarColumn, Progress
from rich.spinner import Spinner
from rich.text import Text
from richpixels import Pixels
from textual import work
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import Reactive
from textual.validation import Length, Validator
from textual.widget import Widget
from textual.widgets import Footer, Input, Label, Placeholder, Static, TextArea
from textual.widgets import Markdown
from vui.audio_utils import playMp3Sound
from vui.vui import Vui


class IntervalUpdater(Static):
    _renderable_object: RenderableType

    def update_rendering(self) -> None:
        self.update(self._renderable_object)

    def on_mount(self) -> None:
        self.interval_update = self.set_interval(1 / 60, self.update_rendering)

    def pause(self) -> None:
        self.interval_update.pause()

    def resume(self) -> None:
        self.interval_update.resume()


class IndeterminateProgressBar(IntervalUpdater):
    """Basic indeterminate progress bar widget based on rich.progress.Progress."""

    def __init__(self) -> None:
        super().__init__("")
        self._renderable_object = Progress(BarColumn())
        self._renderable_object.add_task("", total=None)


class SpinnerWidget(IntervalUpdater):
    """Basic spinner widget based on rich.spinner.Spinner."""

    def __init__(self, name: str, style: str, text: str) -> None:
        super().__init__("")
        self._renderable_object = Spinner(name=name, text=text, style=style)


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
    BINDINGS = [
        ("escape", "close", "close"),
        ("ctrl+d", "close", "close"),
        ("ctrl+s", "submit", "submit"),
    ]

    def action_close(self):
        self.remove()


class Message(Static):
    def __init__(
        self,
        content: RenderableType | object = None,
        classes="",
        id: str | None = None,
        content_style="",
        align_horizontal="center",
    ):
        super().__init__()
        if id is not None:
            self.id = id
        self.content_style = content_style
        self.classes = classes
        self.content = content
        self.highlighter = ReprHighlighter()
        self.styles.align_horizontal = align_horizontal
        self.styles.height = "auto"
        self.styles.margin = 0
        self.can_focus = True

    def _make_renderable(
        self, content: RenderableType | object, style: str = ""
    ) -> RenderableType:
        renderable: RenderableType
        if isinstance(content, str):
            renderable = Text.from_markup(content, style=style)
            renderable = self.highlighter(renderable)
        else:
            renderable = cast(RenderableType, content)

        return renderable

    def compose(self):
        yield Label(
            self._make_renderable(self.content, self.content_style), id="messages"
        )


class UserMessage(Message):
    def __init__(self, icon: str, icon_style: str, **kwargs):
        super().__init__(**kwargs)
        self.icon = icon
        self.styles.align_horizontal = "right"
        self.icon_style = icon_style

    def compose(self):
        yield Label(
            self._make_renderable(self.content, self.content_style), id="user_messages"
        )
        yield Label(self._make_renderable(self.icon, self.icon_style), id="icons")


class AssistantMessage(Message):
    def __init__(self, icon: str, icon_style: str, **kwargs):
        super().__init__(**kwargs)
        self.icon = icon
        self.icon_style = icon_style

    def compose(self):
        yield Label(self._make_renderable(self.icon, self.icon_style), id="icons")
        yield Label(
            self._make_renderable(self.content, self.content_style),
            id="assistant_messages",
        )


class AssistantMessageMd(Message):
    def __init__(self, icon: str, icon_style: str, **kwargs):
        super().__init__(**kwargs)
        self.icon = icon
        self.styles.align_horizontal = "left"
        self.icon_style = icon_style
        self.c = self.content

    def compose(self):
        yield Label(self._make_renderable(self.icon, self.icon_style), id="icons")

    def on_mount(self):
        self.mount(Markdown(str(self.c)))


class PoodleTui(App):

    CSS_PATH = "poodle_tui.tcss"

    BINDINGS = [
        ("k", "toggle_kw_detection", "kw detection"),
        ("ctrl+s", "send", "send"),
        ("s", "input_speech, print_keyword_message", f"speech"),
        ("t", "input_text", "text"),
        ("v", "input_speech", "voice"),
        ("f", "input_file", "parse file"),
        ("ctrl+q", "quit", "quit"),
        ("e", "incr_emote", "increment emote"),
    ]

    async def on_load(self):
        self.config = Configurator()
        self.config.load_configurations()
        self.poodle = Poodle(self.config)
        self.poodle.run()
        self.chat_session = self.poodle.get_session()
        self.kw_listeners = [
            self.kwl_print_keyword_message,
            self.kwl_input_speech,
        ]
        self.poodle_vui = Vui(self.config.keyword, self.kw_listeners, [], self.config)
        self.transcriber = self.poodle_vui.transcriber
        self.keyword_detector = self.poodle_vui.initialize_kw_detector()
        self.tts = self.poodle_vui.tts
        self.tts_local = self.poodle_vui.tts_local
        ef.silence.clear()
        ef.speaking.clear()
        self.chat_utils = self.poodle.chat_utils
        await self.poodle_vui.start_keyword_detection()
        self.transcriber_loop = self.set_interval(0.1, self.loop_transcription)
        self.wrap_width = 112

    def on_mount(self):
        self.status = {
            "transcribing": SpinnerWidget("dots", "blue", "Transcribing..."),
            "vocalizing": SpinnerWidget("dots", "yellow", "Vocalizing..."),
            "replying": SpinnerWidget("dots", "bright_magenta", "Replying..."),
            "reading": SpinnerWidget("dots", "green", "Reading"),
            "listening": Label("Listening"),
            "ready": Label("Ready"),
        }
        for status in self.status:
            self.query_one("#status").mount(self.status[status])
            self.status[status].display = False
        if self.config.sounds:
            # notification-sound-7062.mp3
            self.run_worker(playMp3Sound("sounds/ready.mp3"))

    # shown_configs = Reactive(config.__getstate__)
    auto_send = Reactive(False)
    emote = Reactive(0)
    # 0: neutral, 1:confused, 2:excited, 3:happy, 4:love, 5:angry, 6:dead.
    # assistant_icons = ["󰚩 ", "󱚟 ", "󱚣 ", "󱜙 ","󱚥" "󱚝 ", "󱚡 "]
    assistant_icons = ["󱙺 ", "󱚠 ", "󱚤 ", "󱜚 ", "󱚦 " "󱚞 ", "󱚢 "]

    images = [
        Pixels.from_image_path("images/glyphs0.png"),
        Pixels.from_image_path("images/glyphs1.png"),
        Pixels.from_image_path("images/glyphs2.png"),
        Pixels.from_image_path("images/glyphs3.png"),
        Pixels.from_image_path("images/glyphs4.png"),
        Pixels.from_image_path("images/glyphs5.png"),
        Pixels.from_image_path("images/glyphs6.png"),
    ]

    def action_incr_emote(self):
        if self.emote < 6:
            self.emote = self.emote + 1
        else:
            self.emote = 0

    def compose(self) -> ComposeResult:
        model = self.config.chat_model
        chat_view = VerticalScroll(id="chat_view")
        value_style = "cyan"
        yield Container(
            Static(self.images[0], id="emote"),
            Container(
                Container(
                    Label("Model: "),
                    Label(f"[{value_style}]{model}[/{value_style}]"),
                    classes="infoline",
                    id="model",
                ),
                Container(
                    Label("Agent: "),
                    Label(f"[{value_style}]{self.config.agent_path}[/{value_style}]"),
                    classes="infoline",
                    id="agent",
                ),
                Container(
                    Label("Voice: "),
                    Label(f"[{value_style}]{self.config.voice}[/{value_style}]"),
                    classes="infoline",
                    id="voice_status",
                ),
                Container(
                    Label("keyword: "),
                    Label(f"[{value_style}]{self.config.keyword}[/{value_style}]"),
                    classes="infoline",
                    id="keyword_infoline",
                ),
                Container(
                    Label("temperature: "),
                    Label(f"[{value_style}]{self.config.temperature}[/{value_style}]"),
                    classes="infoline",
                    id="temperature",
                ),
                Container(
                    Label("presence penalty: "),
                    Label(
                        f"[{value_style}]{self.config.presence_penalty}[/{value_style}]"
                    ),
                    classes="infoline",
                    id="presence_penalty",
                ),
                Container(Label("Status: "), classes="infoline", id="status"),
                id="info",
            ),
            Message(self.welcome(), id="welcome"),
            id="header",
        )
        yield chat_view
        yield Footer()

    def welcome(self):
        f = pyfiglet.figlet_format("poodle.", font="slant")
        w = str(
            # f"{f}[bright_magenta]Voice control GPT with rich terminal ui.[/bright_magenta]"
            f"{f}[bright_magenta]Voice interface GPT in your terminal.[/bright_magenta]"
            # "                            v0.04"
            "\n                                v0.04"
        )
        return w

    def isSpeak(self):
        if self.config.speak.lower() != "cloud" or self.config.speak.lower() != "local":
            return False
        return True

    @work
    async def log_response(self, resp, chat_utils) -> None:
        tstamp = FileManager.get_datetime_string()
        FileManager.save_json(
            f"{self.config.response_log_path}response_{tstamp}.json",
            chat_utils.chat_completion_to_dict(resp),
        )

    @work(exclusive=True)
    async def print_response(self, content: str) -> None:
        if content.startswith("@"):
            content = content.lstrip("@")
            c = content.partition("@")
            content = c[2]
            if c[0].isdigit():
                self.emote = int(c[0])
        self.status["replying"].display = False
        content_wrapped = "\n".join(
            textwrap.wrap(
                content,
                width=self.wrap_width,
                replace_whitespace=False,
                drop_whitespace=False,
                break_on_hyphens=False,
                expand_tabs=False,
            )
        )
        if not self.isSpeak():
            self.query_one("#chat_view").mount(
                AssistantMessageMd(
                    content=content,
                    classes="assistant_message_container",
                    icon=f" {self.assistant_icons[self.emote]} >",
                    icon_style="bright_magenta",
                    content_style="medium_orchid3",
                )
            )
        else:
            self.query_one("#chat_view").mount(
                AssistantMessage(
                    content=content_wrapped,
                    classes="assistant_message_container",
                    icon=f" {self.assistant_icons[self.emote]}󰔊 >",
                    icon_style="bright_magenta",
                    content_style="medium_orchid3",
                )
            )

    async def handle_response(self, resp):
        tts_thread = None
        content = self.chat_utils.handle_response(resp, self.chat_session)
        if self.isSpeak():
            tts_thread = self.poodle_vui.speak_response(content)
            tts_thread.start()
        self.print_response(content)
        if tts_thread is not None:
            tts_thread.join()

    @work(thread=True)
    async def send_messages(self) -> None:
        self.status["replying"].display = True
        resp = await self.chat_session.send_chat_request()
        await self.handle_response(resp)

    @work
    async def add_chat_file(self, file_dir):
        file_content = await self.chat_session.add_chat_file(file_dir)
        # file_content_wraped = "\n".join(textwrap.wrap(file_dir, width=self.wrap_width))
        self.query_one("#chat_view").mount(
            UserMessage(
                content=file_content,
                icon="<󰛶  ",
                classes="user-file",
                icon_style="green1",
            )
        )
        self.status["reading"].display = False

    def loop_transcription(self) -> None:
        self.status["transcribing"].display = False
        if ef.silence.is_set() and not ef.recording.is_set():
            self.status["listening"].display = False
            self.status["transcribing"].display = True
            self.poodle_vui.process_transcriptions()
            transcriptions: list = self.poodle_vui.get_transcriptions()
            trans_text = self.chat_utils.extract_trans_text(transcriptions)
            if len(trans_text) == 0:
                if self.config.sounds:
                    self.run_worker(playMp3Sound("sounds/badcopy.mp3"))
                self.query_one("#chat_view").mount(
                    Message(
                        content=" I didn't hear you",
                        classes="local",
                    )
                )
                ef.silence.clear()
                return  # Exit the function early if there's no transcription
            if self.config.sounds:
                self.run_worker(playMp3Sound("sounds/listening.mp3"))
            wrapped_text = "\n".join(
                textwrap.wrap(trans_text[0], width=self.wrap_width)
            )
            self.query_one("#chat_view").mount(
                UserMessage(
                    content=wrapped_text,
                    icon="<󰔊  ",
                    classes="user_voice_container",
                    icon_style="blue",
                    content_style="cyan1",
                )
            )
            if len(str(transcriptions)) != 0:
                self.chat_session.add_user_trans(transcriptions)
            if self.auto_send:
                self.action_send()

    @work
    async def kwl_print_keyword_message(self, keyword, data, stream_write_time) -> None:
        self.status["listening"].display = True
        self.query_one("#chat_view").mount(
            Message(
                f"\n This is {keyword}. I am listening.",
                classes="local",
            )
        )
        if self.config.sounds:
            self.run_worker(playMp3Sound("sounds/listening.mp3"))
        if self.config.speak.lower() == "cloud":
            if self.tts.is_audio_playing():
                self.tts.stop_audio()
        if self.config.speak.lower() == "local":
            self.tts_local.stop_audio()
        else:
            pass

    def action_toggle_voice(self) -> None:
        self.query_one("#chat_view").mount(
            Message(
                f"voice is set to {self.config.speak}",
                classes="local",
            )
        )

    @work
    async def action_print_keyword_message(self) -> None:
        self.status["listening"].display = True
        self.query_one("#chat_view").mount(
            Message(
                f"\n This is {self.config.keyword}. I am listening.",
                classes="local",
            )
        )
        if self.config.sounds:
            self.run_worker(playMp3Sound("sounds/listening.mp3"))
        if self.config.speak.lower() == "cloud":
            if self.tts.is_audio_playing():
                self.tts.stop_audio()
        if self.config.speak.lower() == "local":
            self.tts_local.stop_audio()
        else:
            pass

    def watch_emote(self):
        e = self.emote
        img = self.images[e]
        self.query_one("#emote", Static).update(img)

    @on(Input.Submitted, "#text_input")
    def add_text_input(self, event: Input.Submitted) -> None:
        input = self.query_one("#text_input", TextInput)
        if event.validation_result.is_valid:
            text: str = input.value
            self.chat_session.add_user_text(text)
            text = "\n".join(textwrap.wrap(text, width=self.wrap_width))
            self.query_one("#chat_view").mount(
                UserMessage(
                    content=text,
                    classes="user_text_container",
                    icon="<󰯓  ",
                    icon_style="blue",
                    content_style="cyan3",
                )
            )
        input.remove()

    @on(Input.Submitted, "#file_input")
    def add_file_input(self, event: Input.Submitted) -> None:
        input = self.query_one("#file_input", TextInput)
        if event.validation_result.is_valid:
            self.status["reading"].display = True
            file_dir: str = input.value
            self.add_chat_file(file_dir)
            file_dir = "\n".join(textwrap.wrap(file_dir, width=self.wrap_width))
            self.query_one("#chat_view").mount(
                UserMessage(
                    content=file_dir,
                    icon="<󰛶  ",
                    classes="user-file",
                    icon_style="blue",
                )
            )
        input.remove()

    def action_input_file(self) -> None:
        new_input = TextInput(
            id="file_input",
            valid_empty=False,
            validators=[Length(minimum=2)],
        )
        new_input.border_title = "File"
        self.mount(new_input)
        new_input.focus()

    def action_input_text(self) -> None:
        new_input = TextInput(
            id="text_input",
            validators=[Length(minimum=2)],
            valid_empty=False,
        )
        new_input.border_title = "Text"
        self.app.mount(new_input)
        new_input.focus()

    @work
    async def action_input_speech(self) -> None:
        self.poodle_vui.start_recording()

    @work
    async def kwl_input_speech(self, keyword, data, stream_write_time) -> None:
        self.poodle_vui.start_recording(stream_write_time)

    def action_send(self) -> None:
        # self.mount(Message("send it", align_horizontal="center", classes="info"))
        self.send_messages()

    @work
    async def action_toggle_kw_detection(self) -> None:
        if self.poodle_vui.keyword_detection_active:
            self.poodle_vui.stop_keyword_detection()
            self.query_one("#chat_view").mount(
                Message(
                    "Keyword detection stopped.",
                    classes="local",
                )
            )
        else:
            await self.poodle_vui.start_keyword_detection()
            self.query_one("#chat_view").mount(
                Message(
                    "Keyword detection started.",
                    classes="local",
                )
            )

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


if __name__ == "__main__":
    app = PoodleTui()
    app.run()
