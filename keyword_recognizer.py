# keyword_recognizer.py

import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor

from vosk import Model, KaldiRecognizer

from audio_fetcher import AudioFetcher


class KeywordRecognizer(threading.Thread):

    def __init__(self, keyword, audio_params=None, max_listener_threads=10):
        threading.Thread.__init__(self)

        self.keyword_detected_time = None
        self.start_time = None
        self.wave_file = None
        self.wave_opened = None
        self.keyword = keyword
        self.model = Model(lang='en-us')
        self.audio_queue = queue.Queue()
        self.keyword_listeners = []
        self.partial_listeners = []
        self.running = threading.Event()
        self.running.set()

        self.audio_params = audio_params or {}
        self.fetcher = AudioFetcher(self.audio_queue, self.running, **self.audio_params)
        self.sample_rate = self.fetcher.sample_rate
        self.executor = ThreadPoolExecutor(max_listener_threads)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

    @property
    def get_keyword_detected_time(self):
        return self.keyword_detected_time

    @property
    def get_start_time(self):
        return self.start_time

    def run(self):
        self.fetcher.start()
        try:
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
                    self.notify_keyword_listeners(data)
            partial_result = self.recognizer.PartialResult()
            if partial_result:
                self.notify_partial_listeners(partial_result)
        except queue.Empty:
            print("Queue is empty.")

    def add_keyword_listener(self, listener_func):
        self.keyword_listeners.append(listener_func)

    def notify_keyword_listeners(self, data):
        for listener in self.keyword_listeners:
            self.executor.submit(listener, self.keyword, data)

    def add_partial_listener(self, listener_func):
        self.partial_listeners.append(listener_func)

    def notify_partial_listeners(self, data):
        for listener in self.partial_listeners:
            self.executor.submit(listener, data)

    def close(self):
        self.running.clear()
        self.fetcher.stop()  # use the stop method of AudioFetcher
