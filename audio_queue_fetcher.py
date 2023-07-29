# audio_queue_fetcher.py
import threading
import time
import pyaudio
import config


class AudioQueueFetcher(threading.Thread):
    def __init__(self, audio_queue, running, channels=config.PYAUDIO_CHANNELS, frames_per_buffer=8000):
        threading.Thread.__init__(self)
        self.audio_queue = audio_queue
        self.running = running

        self.pa = pyaudio.PyAudio()
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.default_device_info = self.pa.get_default_input_device_info()
        self.sample_rate = int(self.default_device_info['defaultSampleRate'])

    def run(self):
        stream = self.pa.open(format=config.PYAUDIO_FORMAT,
                              channels=config.PYAUDIO_CHANNELS,
                              rate=self.sample_rate,
                              input=True,
                              frames_per_buffer=config.PYAUDIO_FRAMES_PER_BUFFER)
        while self.running.is_set():
            data = stream.read(self.frames_per_buffer)
            self.audio_queue.put((time.time(), data))
            time.sleep(0.1)
        stream.stop_stream()
        stream.close()
        self.pa.terminate()

    def stop(self):
        self.running.clear()
