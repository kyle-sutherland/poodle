# mock_audio_fetcher.py

import threading
import time
import wave


class MockAudioFetcher(threading.Thread):
    def __init__(self, audio_queue, running, audio_file):
        threading.Thread.__init__(self)
        self.audio_queue = audio_queue
        self.running = running
        self.audio_file = audio_file

    def run(self):
        with wave.open(self.audio_file, 'rb') as wf:
            while self.running.is_set():
                data = wf.readframes(2000)
                self.audio_queue.put((time.time(), data))

    def stop(self):
        self.running.clear()
