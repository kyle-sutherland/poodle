# keyword_recognizer.py

import threading
import queue
from vosk import Model, KaldiRecognizer


from audio_fetcher import AudioFetcher


class KeywordRecognizer(threading.Thread):
    def __init__(self, keyword):
        threading.Thread.__init__(self)
        self.keyword = keyword
        self.model = Model(lang='en-us')
        self.audio_queue = queue.Queue()
        self.listeners = []
        self.running = threading.Event()
        self.running.set()

        self.fetcher = AudioFetcher(self.audio_queue, self.running)
        self.sample_rate = self.fetcher.sample_rate

        self.wave_file = None
        self.wave_opened = False

    def run(self):
        fetcher = AudioFetcher(self.audio_queue, self.running)
        fetcher.start()

        rec = KaldiRecognizer(self.model, self.sample_rate)
        while self.running.is_set() or not self.audio_queue.empty():
            timestamp, data = self.audio_queue.get()
            if rec.AcceptWaveform(data):
                final_result = rec.FinalResult()
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
