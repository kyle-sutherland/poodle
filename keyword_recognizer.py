# keyword_recognizer.py

import threading
import queue
from concurrent.futures import ThreadPoolExecutor

from vosk import Model, KaldiRecognizer

from audio_fetcher import AudioFetcher


class KeywordRecognizer(threading.Thread):
    def __init__(self, keyword, audio_params=None, max_listener_threads=10):
        threading.Thread.__init__(self)

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
        self.executor = ThreadPoolExecutor(max_listener_threads)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

    def run(self):
        self.fetcher.start()
        try:
            rec = KaldiRecognizer(self.model, self.sample_rate)
            while self.running.is_set() or not self.audio_queue.empty():
                self.run_once()
        except Exception as e:
            print(f"An error occurred: {e}")

    def run_once(self):
        try:
            timestamp, data = self.audio_queue.get(timeout=1)  # 1 second timeout
            if self.recognizer.AcceptWaveform(data):
                final_result = self.recognizer.FinalResult()
                if self.keyword in final_result:
                    self.notify_listeners(data)
        except queue.Empty:
            print("Queue is empty.")

    def add_listener(self, listener_func):
        self.listeners.append(listener_func)

    def notify_listeners(self, data):
        for listener in self.listeners:
            self.executor.submit(listener, self.keyword, data)

    def close(self):
        self.running.clear()
        self.fetcher.stop()  # use the stop method of AudioFetcher
        if self.wave_opened:
            self.wave_file.close()
