#!/home/kyle/miniconda3/envs/poodle/bin/python
# poodle_tui.py
from textual.app import App, ComposeResult, RenderResult
from textual.widget import Widget
from textual.widgets import Footer, Static, RichLog, Input
from textual.reactive import Reactive
from textual import work
from textual import on
from rich.text import Text
from rich.spinner import Spinner
import pyfiglet
from rich.console import Console
from rich.markdown import Markdown
import config
from app import Poodle


from audio_utils import (
    playMp3Sound,
)
from file_manager import FileManager
import event_flags as ef

from vui import Vui

console = Console()


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


class TextInput(Input):
    BINDINGS = [("ctrl+m", "submit", "submit")]


class PoodleTui(App):

    BINDINGS = [
        ("d", "toggle_dark", "Dark mode"),
        ("k", "toggle_kw_detection", "toggle kw"),
        ("ctrl+s", "send", f"send to {config.KEYWORD}"),
        ("s", "input_speech, print_keyword_message", f"input speech"),
        ("i", "input_text", "input text"),
        ("v", "toggle_voice", f"toggle voice"),
    ]

    auto_send = Reactive(False)

    def compose(self) -> ComposeResult:
        yield RichLog(
            markup=True, highlight=True, auto_scroll=True, wrap=True, id="main_log"
        )
        yield Footer()

    def welcome(self):
        f = pyfiglet.figlet_format("poodle.", font="slant")
        w = str(
            f"{f}[bright_magenta]Voice interface GPT in your terminal.[/bright_magenta]"
        )
        return w

    async def on_mount(self):
        self.query_one("#main_log", RichLog).write(self.welcome())
        self.poodle = Poodle(config)
        self.poodle.run()
        self.chat_session = self.poodle.get_session()
        self.kw_listeners = [
            self.action_input_speech,
            self.action_print_keyword_message,
        ]
        self.poodle_vui = Vui(config.KEYWORD, self.kw_listeners, [])
        if config.SOUNDS:
            # notification-sound-7062.mp3
            playMp3Sound("./sounds/ready.mp3")
        self.transcriber = self.poodle_vui.transcriber
        self.keyword_detector = self.poodle_vui.initialize_kw_detector()
        self.tts = self.poodle_vui.tts
        self.tts_local = self.poodle_vui.tts_local
        ef.silence.clear()
        ef.speaking.clear()
        self.chat_utils = self.poodle.chat_utils
        await self.poodle_vui.start_keyword_detection()
        self.transcriber_loop = self.set_interval(0.1, self.loop_transcription)
        self.main_log = self.query_one("#main_log", RichLog)

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
        self.main_log.write("")
        self.main_log.write(" 󰚩 > ")
        if not self.isSpeak():
            content_md = Markdown(str(content))
            self.main_log.write(content_md)
        else:
            self.main_log.write(content)

    def handle_response(self, resp, chat):
        tts_thread = None
        content = self.chat_utils.handle_response(resp, chat)
        if self.isSpeak():
            tts_thread = self.poodle_vui.speak_response(content)
            tts_thread.start()
        self.print_response(content)
        if tts_thread is not None:
            tts_thread.join()

    @work
    async def send_message(self, chat):
        resp = await chat.send_request()
        self.handle_response(resp, chat)

    async def loop_transcription(self) -> None:
        if ef.silence.is_set() and not ef.recording.is_set():
            self.poodle_vui.process_transcriptions()
            transcriptions: list = self.poodle_vui.get_transcriptions()
            trans_text = self.chat_utils.extract_trans_text(transcriptions)
            if len(trans_text) == 0:
                if config.SOUNDS:
                    playMp3Sound("./sounds/badcopy.mp3")
                self.main_log.write(" I didn't hear you\n")
                ef.silence.clear()
                return  # Exit the function early if there's no transcription
            if config.SOUNDS:
                playMp3Sound("./sounds/listening.mp3")
            self.main_log.write("[blue] 󰔊 > [/blue]")
            self.main_log.write(trans_text[0])
            if len(str(transcriptions)) != 0:
                self.chat_session.add_user_trans(transcriptions)
            if self.auto_send:
                self.action_send()

    def action_print_keyword_message(self, keyword, data, stream_write_time) -> None:
        self.main_log.write(f"\n This is {keyword}. I am listening.")
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
        config.SPEAK = not config.SPEAK

    @on(Input.Submitted, "#text_input")
    def add_text_input(self):
        input = self.query_one("#text_input", Input)
        input.remove()
        text = input.value
        self.chat_session.add_user_text(text)
        self.main_log.write("[blue] 󰯓 > [/blue]")
        self.main_log.write(text)

    def action_input_text(self):
        new_input = TextInput(id="text_input")
        self.app.mount(new_input)
        new_input.focus()

    def action_input_speech(self, keyword, data, stream_write_time):
        self.poodle_vui.start_recording(stream_write_time)

    def action_send(self) -> None:
        self.main_log.write("send it")
        self.send_message(self.chat_session)

    async def action_toggle_kw_detection(self):
        if self.poodle_vui.keyword_detection_active:
            self.poodle_vui.stop_keyword_detection()
            self.main_log.write("Keyword detection stopped.")
        else:
            await self.poodle_vui.start_keyword_detection()
            self.main_log.write("Keyword detection started.")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark


if __name__ == "__main__":
    app = PoodleTui()
    app.run()
