class PoodleVui:
    def __init__(self):
        self.__init__()
        self.partia_listeners = [
            self.pl_no_speech,
        ]

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

    def initialize_kw_detector(self, kw: str, listeners: list, *partia_listeners: list):
        detector = KeywordDetector(kw)
        if partia_listeners is not None:
            for pl in partia_listeners:
                self.partia_listeners.append(pl)

        for pl in partia_listeners:
            detector.add_partial_listener(pl)

        for l in listeners:
            detector.add_keyword_listener(l)
        # add keyword_detector event listeners
        return detector
