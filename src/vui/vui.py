import threading
import json
import config
import warnings


from vui.audio_utils import (
    KeywordDetector,
    Transcriber,
    OnlineTranscriber,
    AudioRecorder,
    TextToSpeech,
    TextToSpeechLocal,
    SilenceWatcher,
)
import event_flags as ef
from core.file_manager import FileManager


class Vui:
    def __init__(self, kw, listeners: list, partial_listeners: list):
        self.partial_listeners = partial_listeners
        self.listeners = listeners
        self.silence_watcher = SilenceWatcher()
        self.tts = TextToSpeech()
        self.tts_local = TextToSpeechLocal()
        self.audio_recorder = AudioRecorder()
        self.detector = KeywordDetector(kw)
        self.transcriber = self.load_transcriber(config.ONLINE_TRANSCRIBE)
        self.keyword_detection_active = False
        self.transcriptions = []

    def get_transcriptions(self):
        return self.transcriptions

    def speak_response(self, content):
        def tts_task():
            match config.SPEAK.lower():
                case "cloud":
                    self.tts.stream_voice(text=content, voice=config.VOICE)
                case "local":
                    file = self.tts_local.generate_speech(text=content)
                    self.tts_local.play_audio(file)
                case _:
                    pass

        # Start TTS in a separate thread
        return threading.Thread(target=tts_task)

    def load_transcriber(self, online: bool):
        if online:
            return OnlineTranscriber(
                config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH
            )
        return Transcriber(config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH)

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

    def initialize_kw_detector(self):
        self.detector.add_partial_listener(self.pl_no_speech)

        for pl in self.partial_listeners:
            self.detector.add_partial_listener(pl)

        for l in self.listeners:
            self.detector.add_keyword_listener(l)
        # add keyword_detector event listeners
        return self.detector

    def process_transcriptions(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.transcriber.transcribe_bodies()
            self.transcriptions = list(
                FileManager.read_transcriptions(config.TRANSCRIPTION_PATH)
            )

    def start_recording(self, stream_write_time):
        self.audio_recorder.start_recording()
        self.silence_watcher.reset()
        ef.stream_write_time = stream_write_time

    def start_keyword_detection(self):
        self.kw_detection_thread = threading.Thread(target=self.detector.start)
        self.keyword_detection_active = True
        self.kw_detection_thread.start()

    def stop_keyword_detection(self):
        self.detector.close()
        self.keyword_detection_active = False
        self.kw_detection_thread.join()
