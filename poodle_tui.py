# poodle_tui.py
from textual.app import App, ComposeResult, RenderResult
from textual.widget import Widget
from textual.widgets import Footer, Static, RichLog
from textual.reactive import Reactive
from rich.text import Text
from rich.spinner import Spinner


import pyfiglet
from rich.console import Console
from rich.markdown import Markdown
import config
import threading
import json
from app import Poodle
import warnings
import gc
import asyncio

from suppress_stdout_stderr import suppress_stdout_stderr

with suppress_stdout_stderr():
    from audio_utils import (
        KeywordDetector,
        Transcriber,
        OnlineTranscriber,
        AudioRecorder,
        TextToSpeech,
        TextToSpeechLocal,
        SilenceWatcher,
        playMp3Sound,
    )
    from file_manager import FileManager
    import time
    import event_flags as ef

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


class PoodleTui(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keyword_detection_active = (
            False  # State variable to track keyword detection status
        )

    BINDINGS = [
        ("d", "toggle_dark", "Dark mode"),
        ("e", "toggle_kw_detection", "toggle kw"),
    ]

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
        self.mount(SpinnerWidget())
        SpinnerWidget().activate()
        self.keyword_detector = self.initialize_kw_detector(config.KEYWORD)
        self.tts = TextToSpeech()
        self.silence_watcher = SilenceWatcher()
        self.audio_recorder = AudioRecorder()
        self.tts = TextToSpeech()
        self.tts_local = TextToSpeechLocal()
        self.transcriber = self.load_transcriber(config.ONLINE_TRANSCRIBE)
        self.poodle = Poodle(config)
        self.poodle.run()
        self.chat_session = self.poodle.get_session()
        ef.silence.clear()
        ef.speaking.clear()
        self.chat_utils = self.poodle.chat_utils
        self.set_interval(0.1, self.process_transcription_and_send_messages)
        await self.start_keyword_detection()
        self.main_log = self.query_one("#main_log", RichLog)
        if config.SOUNDS:
            # notification-sound-7062.mp3
            playMp3Sound("./sounds/ready.mp3")
        self.call_later(SpinnerWidget().deactivate)
        self.kw_listeners = []

    def initialize_kw_detector(self, kw, listeners, partia_listeners):
        detector = KeywordDetector(kw)
        # add keyword_detector event listeners
        detector.add_keyword_listener(self.action_start_recording)
        # detector.add_keyword_listener(kd_listeners.kwl_stop_audio)
        detector.add_partial_listener(lambda pr: self.pl_no_speech(pr))
        detector.add_keyword_listener(self.action_print_keyword_message)
        return detector

    def isSpeak(self):
        if (
            config.SPEAK is not None
            or config.SPEAK != ""
            or config.SPEAK.lower() != "none"
        ):
            return True
        return False

    def speak_response(self, content):
        def tts_task():
            match config.SPEAK.lower():
                case "cloud":
                    tts = TextToSpeech()
                    tts.stream_voice(text=content, voice=config.VOICE)
                case "local":
                    tts_local = TextToSpeechLocal()
                    file = tts_local.generate_speech(text=content)
                    tts_local.play_audio(file)
                case _:
                    pass

        # Start TTS in a separate thread
        return threading.Thread(target=tts_task)

    def log_response(self, resp, chat_utils):
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
        content = resp.choices[0].message.content
        tts_thread = None
        if self.isSpeak():
            tts_thread = self.speak_response(content)
            tts_thread.start()
        if not config.STREAM_RESPONSE:
            chat.add_reply_entry(resp)
            self.print_response(content)
            if chat.is_model_near_limit_thresh(resp):
                s = chat.summarize_conversation()
                chat.add_summary(s)
        # BROKEN don't use
        # TODO: fix this
        else:
            chat.extract_streamed_resp_deltas(resp)
        if tts_thread is not None:
            tts_thread.join()
        ef.silence.clear()
        gc.collect()

    def send_message(self, chat):
        resp = chat.send_request()
        self.handle_response(resp, chat)

    async def process_transcription_and_send_messages(self):
        # This function replaces the part of start_keyword_detection related to transcription and sending messages
        if ef.silence.is_set() and not ef.recording.is_set():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                await asyncio.to_thread(self.transcriber.transcribe_bodies)
            transcriptions = FileManager.read_transcriptions(config.TRANSCRIPTION_PATH)
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
            if len(transcriptions) != 0:
                self.chat_session.add_user_trans(transcriptions)
            self.send_message(self.chat_session)

    def load_transcriber(self, online: bool):
        if online:
            return OnlineTranscriber(
                config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH
            )
        return Transcriber(config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH)

    def action_print_keyword_message(self, keyword, data, stream_write_time):
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

    def action_start_recording(self, keyword, data, stream_write_time):
        self.audio_recorder.start_recording()
        self.silence_watcher.reset()
        ef.stream_write_time = stream_write_time

    async def start_keyword_detection(self):
        self.kw_detection_thread = threading.Thread(target=self.keyword_detector.start)
        self.keyword_detection_active = True
        self.kw_detection_thread.start()

    def stop_keyword_detection(self):
        self.keyword_detector.close()
        self.keyword_detection_active = False
        self.kw_detection_thread.join()

    async def action_toggle_kw_detection(self):
        if self.keyword_detection_active:
            self.stop_keyword_detection()  # Stop keyword detection
            self.main_log.write("Keyword detection stopped.")
        else:
            await self.start_keyword_detection()  # Start keyword detection
            self.main_log.write("Keyword detection started.")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def pl_no_speech(self, partial_result):
        pr = json.loads(partial_result)
        if ef.recording.is_set():
            if self.silence_watcher.check_silence(pr):
                ef.silence.set()
                timestamp = FileManager.get_datetime_string()
                self.audio_recorder.stop_recording(
                    f"{config.PATH_PROMPT_BODIES_AUDIO}body_{timestamp}.wav"
                )
                self.silence_watcher.reset()


if __name__ == "__main__":
    app = PoodleTui()
    app.run()
