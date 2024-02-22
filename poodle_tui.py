# poodle_tui.py
import textwrap
from typing import cast

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
from textual.validation import Length, Number
from textual.widgets import (
    Footer,
    Input,
    Label,
    Placeholder,
    Static,
    TextArea,
    Select,
    Markdown,
    Switch,
)
from textual.widget import Widget

from config import Configurator
from core.core import Poodle
from core.file_manager import FileManager
import event_flags as ef
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


class OptionsMenu(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_focus = True

    BINDINGS = [("o", "close", "close")]

    def compose(self):
        tempinput = Input(
            type="number",
            value=str(PoodleTui().config.temperature),
            validators=[Number(minimum=0.0, maximum=2.0)],
            id="opt_temp",
        )
        ppinput = Input(
            type="number",
            value=str(PoodleTui().config.presence_penalty),
            validators=[Number(minimum=0.0, maximum=2.0)],
            id="opt_pp",
        )
        tts_opts = ["none", "cloud", "local"]
        yield Container(
            Label("Voice: "),
            Select(
                options=(
                    (voice, voice) for voice in PoodleTui().whisper_info["voices"]
                ),
                value=PoodleTui().config.voice,
                allow_blank=False,
                id="opt_voice",
            ),
            Label("Model:"),
            Select(
                options=((model, model) for model in PoodleTui().chat_models),
                value=PoodleTui().config.chat_model,
                allow_blank=False,
                id="opt_chat_model",
            ),
            Label("temperature: "),
            tempinput,
            Label("presence penalty: "),
            ppinput,
            Label("Sounds:"),
            Switch(value=PoodleTui().config.sounds, id="opt_sounds"),
            Label("Speech Output:"),
            Select(
                options=((opt, opt) for opt in tts_opts),
                value=PoodleTui().config.tts,
                allow_blank=False,
                id="opt_speech",
            ),
            id="opts_0",
        )

    def action_close(self):
        self.remove()


class PoodleTui(App):

    CSS_PATH = "poodle_tui.tcss"

    BINDINGS = [
        # ("k", "toggle_kw_detection", "kw detection"),
        ("ctrl+s", "send", "send"),
        ("s", "input_speech, print_keyword_message", f"speech"),
        ("t", "input_text", "text"),
        ("v", "input_speech", "voice"),
        ("f", "input_file", "parse file"),
        ("ctrl+q", "quit", "quit"),
        ("o", "options", "options"),
    ]

    images = [
        Pixels.from_image_path("images/glyphs0.png"),
        Pixels.from_image_path("images/glyphs1.png"),
        Pixels.from_image_path("images/glyphs2.png"),
        Pixels.from_image_path("images/glyphs3.png"),
        Pixels.from_image_path("images/glyphs4.png"),
        Pixels.from_image_path("images/glyphs5.png"),
        Pixels.from_image_path("images/glyphs6.png"),
    ]

    config = Configurator()
    whisper_info: dict = FileManager.read_json("whisper.json")
    chat_models: dict = FileManager.read_json("core/models.json")

    async def on_load(self):
        self.config.load_configurations()
        self.poodle = Poodle(self.config)
        self.poodle.run()
        self.chat_session = self.poodle.get_session()
        self.chat_utils = self.poodle.chat_utils
        self.kw_listeners = [
            self.kwl_print_keyword_message,
            self.kwl_input_speech,
        ]
        self.vui = Vui(self.config.keyword, self.kw_listeners, [], self.config)
        self.transcriber = self.vui.transcriber
        self.keyword_detector = self.vui.initialize_kw_detector()
        self.tts = self.vui.tts
        self.tts_local = self.vui.tts_local
        ef.silence.clear()
        ef.speaking.clear()
        await self.vui.start_keyword_detection()
        self.transcriber_loop = self.set_interval(0.1, self.loop_transcription)
        self.wrap_width = 112

    def on_mount(self):
        for status in self.status:
            self.query_one("#status").mount(self.status[status])
            self.status[status].display = False
        if self.config.sounds:
            # notification-sound-7062.mp3
            self.run_worker(playMp3Sound("sounds/ready.mp3"))
        self.query_one("#chat_view").mount(Message(self.welcome()))

    # 0: neutral, 1:confused, 2:excited, 3:happy, 4:love, 5:angry, 6:dead.
    # assistant_icons = ["󰚩 ", "󱚟 ", "󱚣 ", "󱜙 ","󱚥 " "󱚝 ", "󱚡 "]
    assistant_icons = ["󱙺 ", "󱚠 ", "󱚤 ", "󱜚 ", "󱚦 " "󱚞 ", "󱚢 "]
    status = {
        "transcribing": SpinnerWidget("dots", "blue", "Transcribing..."),
        "vocalizing": SpinnerWidget("dots", "yellow", "Vocalizing..."),
        "replying": SpinnerWidget("dots", "bright_magenta", "Replying..."),
        "reading": SpinnerWidget("dots", "green", "Reading"),
        "listening": Label("Listening"),
        "ready": Label("Ready"),
    }
    auto_send = Reactive(False)
    emote = Reactive(0)

    def config_label_str(self, value) -> str:
        config_value_style = "cyan"
        return f"[{config_value_style}]{value}[/{config_value_style}]"

    def config_label_bool(self, value: bool) -> str:
        if value:
            return f"[bright_green]{value}[/bright_green]"
        else:
            return f"[red]{value}[/red]"

    def compose(self) -> ComposeResult:
        chat_view = VerticalScroll(id="chat_view")
        yield Container(
            Static(self.images[0], id="emote"),
            Container(
                Container(
                    Label("Model: "),
                    Label(
                        self.config_label_str(self.config.chat_model),
                        id="model_infoline",
                    ),
                    classes="infoline",
                ),
                Container(
                    Label("Agent: "),
                    Label(
                        self.config_label_str(self.config.agent_path),
                        id="agent_infoline",
                    ),
                    classes="infoline",
                ),
                Container(
                    Label("Text To Speech: "),
                    Label(self.config_label_str(self.config.tts), id="tts_infoline"),
                    classes="infoline",
                ),
                Container(
                    Label("Voice: "),
                    Label(
                        self.config_label_str(self.config.voice),
                        id="voice_infoline",
                    ),
                    classes="infoline",
                ),
                Container(
                    Label("Sounds: "),
                    Label(
                        self.config_label_bool(self.config.sounds),
                        id="sounds_infoline",
                    ),
                    classes="infoline",
                ),
                Container(
                    Label("keyword: "),
                    Label(
                        self.config_label_str(self.config.keyword),
                        id="keyword_infoline",
                    ),
                    classes="infoline",
                ),
                Container(
                    Label("Detector: "),
                    Label(
                        self.config_label_bool(self.vui.keyword_detection_active),
                        id="detector_infoline",
                    ),
                    classes="infoline",
                ),
                Container(
                    Label("temperature: "),
                    Label(
                        self.config_label_str(self.config.temperature),
                        id="temperature_infoline",
                    ),
                    classes="infoline",
                ),
                Container(
                    Label("presence penalty: "),
                    Label(
                        self.config_label_str(self.config.presence_penalty),
                        id="presence_penalty_infoline",
                    ),
                    classes="infoline",
                ),
                Container(Label("Status: "), classes="infoline", id="status"),
                id="info",
            ),
            id="extrapane",
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
        if self.config.tts.lower() != "cloud" or self.config.tts.lower() != "local":
            return False
        return True

    def watch_emote(self):
        e = self.emote
        img = self.images[e]
        self.query_one("#emote", Static).update(img)

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
            tts_thread = self.vui.speak_response(content)
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
            self.vui.process_transcriptions()
            transcriptions: list = self.vui.get_transcriptions()
            trans_text = self.chat_utils.extract_trans_text(transcriptions)
            if len(trans_text) == 0:
                if self.config.sounds:
                    self.run_worker(playMp3Sound("sounds/badcopy.mp3"))
                self.query_one("#chat_view").mount(
                    Message(
                        content=" I didn't hear you",
                        classes="local",
                        content_style="bright_magenta",
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

    # keyword listeners
    @work
    async def kwl_input_speech(self, keyword, data, stream_write_time) -> None:
        self.vui.start_recording(stream_write_time)

    @work
    async def kwl_print_keyword_message(self, keyword, data, stream_write_time) -> None:
        self.status["listening"].display = True
        self.query_one("#chat_view").mount(
            Message(
                f"\n This is {keyword}. I am listening.",
                classes="local",
                content_style="bright_magenta",
            )
        )
        if self.config.sounds:
            self.run_worker(playMp3Sound("sounds/listening.mp3"))
        if self.config.tts.lower() == "cloud":
            if self.tts.is_audio_playing():
                self.tts.stop_audio()
        if self.config.tts.lower() == "local":
            self.tts_local.stop_audio()
        else:
            pass

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

    @on(Select.Changed, "#opt_voice")
    def select_voice_changed(self, event: Select.Changed):
        voice: str = str(event.value)
        self.action_edit_voice(voice)
        self.title = voice

    @on(Select.Changed, "#opt_chat_model")
    def select_chat_model_changed(self, event: Select.Changed):
        model: str = str(event.value)
        self.action_edit_chat_model(model)
        self.title = model

    @on(Input.Submitted, "#opt_temp")
    def opt_temp_changed(self, event: Input.Submitted):
        temp: float = float(event.value)
        self.action_edit_temperature(temp)

    @on(Input.Submitted, "#opt_pp")
    def opt_pp_changed(self, event: Input.Submitted):
        pp: float = float(event.value)
        self.action_edit_presence_penalty(pp)

    @on(Switch.Changed, "#opt_sounds")
    def opt_sounds_changed(self):
        self.action_toggle_sounds()

    @on(Select.Changed, "#opt_speech")
    def opt_speech_changed(self, event: Select.Changed):
        speech = str(event.value)
        self.action_edit_config_tts(speech)

    def action_options(self) -> None:
        opts = OptionsMenu()
        self.mount(opts)
        opts.focus()

    def action_input_file(self) -> None:
        new_input = TextInput(
            id="file_input",
            valid_empty=False,
            validators=[Length(minimum=2)],
        )
        new_input.border_title = "File"
        self.query_one("#chat_view").mount(new_input)
        new_input.focus()

    @work
    async def action_print_keyword_message(self) -> None:
        self.status["listening"].display = True
        self.query_one("#chat_view").mount(
            Message(
                f"\n This is {self.config.keyword}. I am listening.",
                classes="local",
                content_style="bright_magenta",
            )
        )
        if self.config.sounds:
            self.run_worker(playMp3Sound("sounds/listening.mp3"))
        if self.config.tts.lower() == "cloud":
            if self.tts.is_audio_playing():
                self.tts.stop_audio()
        if self.config.tts.lower() == "local":
            self.tts_local.stop_audio()
        else:
            pass

    def action_incr_emote(self):
        if self.emote < 6:
            self.emote = self.emote + 1
        else:
            self.emote = 0

    def action_input_text(self) -> None:
        new_input = TextInput(
            id="text_input",
            validators=[Length(minimum=2)],
            valid_empty=False,
        )
        new_input.border_title = "Text"
        self.query_one("#chat_view").mount(new_input)
        new_input.focus()

    @work
    async def action_input_speech(self) -> None:
        self.vui.start_recording()

    def action_send(self) -> None:
        # self.mount(Message("send it", align_horizontal="center", classes="info"))
        self.send_messages()

    @work
    async def action_toggle_kw_detection(self) -> None:
        if self.vui.keyword_detection_active:
            self.vui.stop_keyword_detection()
        else:
            await self.vui.start_keyword_detection()
        self.query_one("#detector_infoline", Label).update(
            self.config_label_bool(self.vui.keyword_detection_active)
        )

    def action_toggle_sounds(self) -> None:
        if self.config.sounds:
            self.config.__setattr__("sounds", False)
        else:
            self.config.__setattr__("sounds", True)
        self.query_one("#sounds_infoline", Label).update(
            self.config_label_bool(self.config.sounds)
        )

    def action_toggle_online_transcribe(self) -> None:
        if self.config.online_transcribe:
            self.config.__setattr__("online_transcribe", False)
        else:
            self.config.__setattr__("online_transcribe", True)
        # self.query_one("#online_transcribe_infoline", Label).update(
        #     self.config_label_str(self.config.online_transcribe)
        # )

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_edit_config_tts(self, tts: str) -> None:
        self.config.__setattr__("tts", tts)
        self.query_one("#tts_infoline", Label).update(
            self.config_label_str(self.config.tts)
        )

    def action_edit_temperature(self, temp: float) -> None:
        if temp > 2.0:
            temp = 2.0
        if temp < 0:
            temp = 0
        self.config.__setattr__("temperature", temp)
        self.query_one("#temperature_infoline", Label).update(
            self.config_label_str(self.config.temperature)
        )

    def action_edit_presence_penalty(self, pp: float) -> None:
        if pp > 2.0:
            pp = 2.0
        if pp < 0:
            pp = 0
        self.config.__setattr__("presence_penalty", pp)
        self.query_one("#presence_penalty_infoline", Label).update(
            self.config_label_str(self.config.tts)
        )

    def action_edit_chat_model(self, chat_model: str) -> None:
        self.config.__setattr__("chat_model", chat_model)
        self.query_one("#model_infoline", Label).update(
            self.config_label_str(self.config.chat_model)
        )

    def action_edit_agent_path(self, agent_path: str) -> None:
        self.config.__setattr__("agent_path", agent_path)
        self.query_one("#agent_infoline", Label).update(
            self.config_label_str(self.config.agent_path)
        )

    def action_edit_keyword(self, keyword: str) -> None:
        self.config.__setattr__("keyword", keyword)
        self.query_one("#keyword_infoline", Label).update(
            self.config_label_str(self.config.keyword)
        )

    def action_edit_voice(self, voice: str) -> None:
        self.config.__setattr__("voice", voice)
        self.query_one("#voice_infoline", Label).update(
            self.config_label_str(self.config.voice)
        )


if __name__ == "__main__":
    app = PoodleTui()
    app.run()
