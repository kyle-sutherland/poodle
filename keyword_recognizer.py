# keyword_recognizer.py

import threading
import queue
from vosk import Model, KaldiRecognizer

from audio_fetcher import AudioFetcher


class KeywordRecognizer(threading.Thread):
    def __init__(self, keyword, audio_params=None):
        threading.Thread.__init__(self)
        self.recognizer = None
        self.wave_file = None
        self.wave_opened = None
        self.keyword = keyword
        self.model = Model(lang='en-us')
        self.audio_queue = queue.Queue()
        self.listeners = []
        self.running = threading.Event()
        self.running.set()

        self.audio_params = audio_params or {}
        self.fetcher = AudioFetcher(self.audio_queue, self.running, **self.audio_params)
        self.sample_rate = self.fetcher.sample_rate

    def run(self):
        self.fetcher.start()
        rec = KaldiRecognizer(self.model, self.sample_rate)
        while self.running.is_set() or not self.audio_queue.empty():
            self.run_once()

    def run_once(self):
        if self.recognizer is None:
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        timestamp, data = self.audio_queue.get()
        if self.recognizer.AcceptWaveform(data):
            final_result = self.recognizer.FinalResult()
            if self.keyword in final_result:
                self.notify_listeners(data)

    def add_listener(self, listener_func):
        self.listeners.append(listener_func)

    def notify_listeners(self, data):
        for listener in self.listeners:
            listener_thread = threading.Thread(target=listener, args=(self.keyword, data))
            listener_thread.start()

    def close(self):
        self.running.clear()
        if self.wave_opened:
            self.wave_file.close()
